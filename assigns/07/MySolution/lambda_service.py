"""Adapter between JSON-RPC methods and the provided LAMBDA3 implementation."""

from __future__ import annotations

import multiprocessing
import os
import sys
import time
from functools import lru_cache
from pathlib import Path
from multiprocessing.connection import Connection
from multiprocessing.connection import wait

LAMBDA3_DIR = Path(__file__).resolve().parents[1] / "LAMBDA3"
if str(LAMBDA3_DIR) not in sys.path:
    sys.path.insert(0, str(LAMBDA3_DIR))

import lambda3 as lambda3  # type: ignore[reportMissingImports]

MAX_SOURCE_CHARACTERS = 65_536
INTERPRETATION_TIMEOUT_SECONDS = 2.0
INTERPRETATION_RECURSION_LIMIT = 1_000_000

LambdaSyntaxError = lambda3.LambdaSyntaxError
TypeCheckError = lambda3.TypeCheckError


class ExecutionTimeout(Exception):
    """Raised when an isolated interpretation worker exceeds its deadline."""

    def __init__(self, timeout_seconds: float) -> None:
        super().__init__(timeout_seconds)
        self.timeout_seconds = timeout_seconds


def _interpret_in_worker(
    connection: Connection,
    expression: lambda3.d0exp,
) -> None:
    sys.setrecursionlimit(INTERPRETATION_RECURSION_LIMIT)
    devnull = open(os.devnull, "w", encoding="utf-8")
    sys.stdout = devnull
    sys.stderr = devnull
    try:
        value = lambda3.d0exp_evaluate(expression)
        connection.send(("ok", lambda3.d0val_format(value)))
    except Exception as error:
        connection.send(("error", type(error).__name__, str(error)))
    finally:
        connection.close()
        devnull.close()


def _parse_and_typecheck(
    source: str,
) -> tuple[lambda3.d0exp, lambda3.simple_type]:
    try:
        return lambda3.d0exp_parse_and_typecheck(source)
    except TypeCheckError:
        expression = lambda3.d0exp_parse(source)
        wrapped = lambda3.D0Elets(_standard_library_declarations(), expression)
        return wrapped, lambda3.d0exp_typecheck(wrapped)


@lru_cache(maxsize=1)
def _standard_library_declarations():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((LAMBDA3_DIR / "mylib").glob("*.lam"))
    )
    declarations = lambda3.d0cls_parse(source)
    lambda3.d0cls_typecheck(declarations)
    return declarations


class LambdaService:
    """Small service adapter that validates source and invokes LAMBDA3."""

    def __init__(
        self,
        timeout_seconds: float = INTERPRETATION_TIMEOUT_SECONDS,
    ) -> None:
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _parse_and_typecheck(
        source: str,
    ) -> tuple[lambda3.d0exp, lambda3.simple_type]:
        return _parse_and_typecheck(source)

    def typecheck(self, source: str) -> dict[str, str]:
        _, typ = self._parse_and_typecheck(source)
        return {"type": lambda3.format_type(typ)}

    def interpret(self, source: str) -> dict[str, str]:
        expression, typ = self._parse_and_typecheck(source)
        value = self._evaluate_with_deadline(expression)
        return {"type": lambda3.format_type(typ), "value": value}

    def compile(self, source: str, target: str) -> dict[str, str]:
        expression, _ = self._parse_and_typecheck(source)
        if target == "python":
            code = lambda3.d0exp_compile(expression)
        else:
            code = lambda3.d0exp_compile_js(expression)
        return {"target": target, "code": code}

    def _evaluate_with_deadline(self, expression: lambda3.d0exp) -> str:
        context = multiprocessing.get_context("spawn")
        parent_connection, child_connection = context.Pipe(duplex=False)
        worker = context.Process(
            target=_interpret_in_worker,
            args=(child_connection, expression),
            daemon=True,
        )
        try:
            worker.start()
            child_connection.close()
            deadline = time.monotonic() + self.timeout_seconds
            remaining = max(0.0, deadline - time.monotonic())
            ready = wait(
                [parent_connection, worker.sentinel],
                timeout=remaining,
            )
            if time.monotonic() >= deadline:
                raise ExecutionTimeout(self.timeout_seconds)
            if parent_connection not in ready:
                if worker.sentinel in ready:
                    worker.join()
                    raise RuntimeError("LAMBDA3 worker exited without a result")
                raise ExecutionTimeout(self.timeout_seconds)
            message = parent_connection.recv()
            worker.join(timeout=0.1)
            if worker.is_alive():
                worker.terminate()
                worker.join()
            if not message or message[0] != "ok":
                detail = message[2] if len(message) > 2 else "worker failed"
                raise RuntimeError(f"LAMBDA3 worker failed: {detail}")
            return message[1]
        finally:
            parent_connection.close()
            if child_connection:
                child_connection.close()
            if worker.pid is not None and worker.is_alive():
                worker.terminate()
                worker.join()
