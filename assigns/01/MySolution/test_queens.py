#!/usr/bin/env python3
"""Run the same output-based regression tests for queens.dats and queens.py.

The two programs are intentionally fixed, no-input eight-queens programs.
This script therefore tests their observable standard output instead of adding
test-only inputs or changing either implementation.  It compiles a temporary
copy of the ATS source when ``patscc`` is installed, or an existing compiled
ATS executable can be supplied with ``--ats-executable``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Callable


ROOT = Path(__file__).resolve().parent
N = 8
INITIAL_BOARD = tuple(range(N))


@dataclass
class ProgramRun:
    """The outcome of starting one of the two programs."""

    name: str
    status: str
    output: str = ""
    raw_output: bytes = b""
    detail: str = ""


def expected_row(column: int) -> str:
    return ". " * column + "Q " + ". " * (N - column - 1)


def run_command(name: str, command: list[str]) -> ProgramRun:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return ProgramRun(name, "FAIL", detail=str(error))

    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        detail = detail or f"exit code {completed.returncode}"
        return ProgramRun(
            name,
            "FAIL",
            output=completed.stdout.decode("utf-8", errors="replace"),
            raw_output=completed.stdout,
            detail=detail,
        )
    return ProgramRun(
        name,
        "READY",
        output=completed.stdout.decode("utf-8", errors="replace"),
        raw_output=completed.stdout,
    )


def run_python() -> ProgramRun:
    return run_command("Python", [sys.executable, str(ROOT / "queens.py")])


def run_ats(executable: Path | None) -> ProgramRun:
    if executable is not None:
        if not executable.is_file():
            return ProgramRun("ATS", "UNAVAILABLE", detail=f"not found: {executable}")
        return run_command("ATS", [str(executable)])

    patscc = shutil.which("patscc") or shutil.which("patscc.exe")
    if patscc is None:
        return ProgramRun(
            "ATS",
            "UNAVAILABLE",
            detail="patscc is not on PATH; use --ats-executable after compiling queens.dats",
        )

    # Compile outside the repository so a test run never changes the submitted
    # ATS source or leaves generated compiler files beside it.
    with tempfile.TemporaryDirectory(prefix="queens-ats-") as temporary_dir:
        build_dir = Path(temporary_dir)
        source_copy = build_dir / "queens.dats"
        shutil.copy2(ROOT / "queens.dats", source_copy)
        executable_name = "queens_ats.exe" if sys.platform == "win32" else "queens_ats"
        compiled_program = build_dir / executable_name
        try:
            compilation = subprocess.run(
                [patscc, "-DATS_MEMALLOC_LIBC", "-o", str(compiled_program), str(source_copy)],
                cwd=build_dir,
                capture_output=True,
            timeout=60,
            check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return ProgramRun("ATS", "FAIL", detail=f"compilation failed: {error}")

        if compilation.returncode != 0:
            detail = compilation.stderr.decode("utf-8", errors="replace").strip()
            detail = detail or f"compiler exit code {compilation.returncode}"
            return ProgramRun("ATS", "FAIL", detail=f"compilation failed: {detail}")
        return run_command("ATS", [str(compiled_program)])


def parsed_solutions(output: str) -> list[tuple[int, tuple[int, ...]]]:
    """Parse the exact fixed-format solution boards printed by either program."""
    lines = output.splitlines()
    index = 9  # eight initial-board rows followed by one blank line
    solutions: list[tuple[int, tuple[int, ...]]] = []

    while index < len(lines):
        if index + 10 > len(lines):
            raise AssertionError("truncated solution output")
        header = lines[index]
        if not header.startswith("Solution #") or not header.endswith(":"):
            raise AssertionError(f"expected a solution header at line {index + 1}")
        try:
            number = int(header.removeprefix("Solution #").removesuffix(":"))
        except ValueError as error:
            raise AssertionError(f"malformed solution header: {header!r}") from error
        if lines[index + 1] != "":
            raise AssertionError(f"solution #{number} is missing its blank line")

        columns: list[int] = []
        for row in lines[index + 2 : index + 10]:
            cells = row.split()
            if len(cells) != N or cells.count("Q") != 1 or any(cell not in {".", "Q"} for cell in cells):
                raise AssertionError(f"solution #{number} has an invalid board row: {row!r}")
            column = cells.index("Q")
            if row != expected_row(column):
                raise AssertionError(f"solution #{number} does not preserve board spacing")
            columns.append(column)
        if lines[index + 10] != "":
            raise AssertionError(f"solution #{number} is missing its trailing blank line")
        solutions.append((number, tuple(columns)))
        index += 11

    return solutions


def test_initial_board(output: str) -> str:
    lines = output.splitlines()
    expected = [expected_row(column) for column in INITIAL_BOARD]
    if lines[:8] != expected or len(lines) < 9 or lines[8] != "":
        raise AssertionError("the initial diagonal eight-queen board is not printed exactly")
    return "initial diagonal board and its blank separator are exact"


def test_solution_count_and_numbering(output: str) -> str:
    solutions = parsed_solutions(output)
    numbers = [number for number, _ in solutions]
    if numbers != list(range(1, 93)):
        raise AssertionError(f"expected solution numbers 1 through 92, got {numbers!r}")
    return "92 solutions are numbered consecutively from 1 through 92"


def test_solution_validity(output: str) -> str:
    solutions = parsed_solutions(output)
    for number, board in solutions:
        if len(set(board)) != N:
            raise AssertionError(f"solution #{number} repeats a column")
        for row, column in enumerate(board):
            for earlier_row, earlier_column in enumerate(board[:row]):
                if abs(row - earlier_row) == abs(column - earlier_column):
                    raise AssertionError(f"solution #{number} has a diagonal conflict")
    return "every printed board has eight non-attacking queens"


TEST_CASES: tuple[tuple[str, Callable[[str], str]], ...] = (
    ("1. Boundary/unusual initial board", test_initial_board),
    ("2. Normal complete search", test_solution_count_and_numbering),
    ("3. Additional solution-validity check", test_solution_validity),
)


def test_program(run: ProgramRun, test: Callable[[str], str]) -> tuple[str, str]:
    if run.status == "UNAVAILABLE":
        return "SKIPPED", run.detail
    if run.status == "FAIL":
        return "FAIL", run.detail
    try:
        return "PASS", test(run.output)
    except AssertionError as error:
        return "FAIL", str(error)


def print_result(program: str, status: str, detail: str) -> None:
    print(f"  {program:<6} {status}: {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ats-executable",
        type=Path,
        help="path to a precompiled executable made from queens.dats",
    )
    args = parser.parse_args()

    ats_run = run_ats(args.ats_executable)
    python_run = run_python()
    failed = False

    print("Eight-Queens ATS/Python Regression Tests")
    print("Programs use their original fixed no-input behavior.\n")
    for title, test in TEST_CASES:
        print(title)
        ats_status, ats_detail = test_program(ats_run, test)
        python_status, python_detail = test_program(python_run, test)
        print_result("ATS", ats_status, ats_detail)
        print_result("Python", python_status, python_detail)
        if ats_status == "PASS" and python_status == "PASS":
            if ats_run.raw_output == python_run.raw_output:
                print_result("Match", "PASS", "ATS and Python standard output is identical")
            else:
                print_result("Match", "FAIL", "ATS and Python standard output differs")
                failed = True
        else:
            print_result("Match", "SKIPPED", "both successful program runs are required")
        print()
        failed = failed or ats_status == "FAIL" or python_status == "FAIL"

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
