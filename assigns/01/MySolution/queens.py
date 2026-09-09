#!/usr/bin/env python3
"""Python 3 translation of queens.dats.

The program intentionally solves the fixed eight-queens problem, prints the
initial diagonal board, enumerates its solutions in the same depth-first order
as the ATS original, and verifies that there are 92 solutions.
"""

N = 8  # As in queens.dats, this is not intended to be changed.


def print_dots(i: int) -> None:
    """Print i empty cells, preserving the ATS program's trailing spaces."""
    if i > 0:
        print(". ", end="")
        print_dots(i - 1)


def print_row(i: int) -> None:
    print_dots(i)
    print("Q ", end="")
    print_dots(N - i - 1)
    print()


def print_board(board: tuple[int, int, int, int, int, int, int, int]) -> None:
    for column in board:
        print_row(column)
    print()


def board_get(board: tuple[int, int, int, int, int, int, int, int], i: int) -> int:
    """Match the original's out-of-range result of zero."""
    if 0 <= i < N:
        return board[i]
    return 0


def board_set(
    board: tuple[int, int, int, int, int, int, int, int], i: int, j: int
) -> tuple[int, int, int, int, int, int, int, int]:
    """Return a new board, leaving board unchanged for an invalid row index."""
    if 0 <= i < N:
        return board[:i] + (j,) + board[i + 1 :]
    return board


def safety_test1(i0: int, j0: int, i: int, j: int) -> bool:
    return j0 != j and abs(i0 - i) != abs(j0 - j)


def safety_test2(
    i0: int, j0: int, board: tuple[int, int, int, int, int, int, int, int], i: int
) -> bool:
    if i >= 0:
        if safety_test1(i0, j0, i, board_get(board, i)):
            return safety_test2(i0, j0, board, i - 1)
        return False
    return True


def search(
    board: tuple[int, int, int, int, int, int, int, int], i: int, j: int, nsol: int
) -> int:
    """Search in the same order and with the same backtracking as queens.dats.

    Each recursive call in the ATS source is a tail call.  This loop performs
    those same state transitions without relying on tail-call optimization,
    which CPython does not implement.
    """
    while True:
        if j < N:
            if safety_test2(i, j, board, i - 1):
                next_board = board_set(board, i, j)
                if i + 1 == N:
                    print(f"Solution #{nsol + 1}:\n")
                    print_board(next_board)
                    # search(board, i, j + 1, nsol + 1)
                    j += 1
                    nsol += 1
                else:
                    # search(next_board, i + 1, 0, nsol)
                    board = next_board
                    i += 1
                    j = 0
            else:
                # search(board, i, j + 1, nsol)
                j += 1
        elif i > 0:
            # search(board, i - 1, board_get(board, i - 1) + 1, nsol)
            j = board_get(board, i - 1) + 1
            i -= 1
        else:
            return nsol


def main() -> None:
    print_board((0, 1, 2, 3, 4, 5, 6, 7))
    nsol = search((0, 0, 0, 0, 0, 0, 0, 0), 0, 0, 0)
    assert nsol == 92


if __name__ == "__main__":
    main()
