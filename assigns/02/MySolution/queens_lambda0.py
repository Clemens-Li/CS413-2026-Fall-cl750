"""Interpreter-executed LAMBDA0 n-queens translation (counts all solutions)."""
from lambda0 import (T0Mint, T0Mbtf, T0Mapp, T0Mfix, T0Mif0, T0Mlam, T0Mop2, T0Mpair, T0Mpfst, T0Mpsnd, T0Mvar, t0erm_cbv_evaluate0)

def app(f, *xs):
    for x in xs:
        f = T0Mapp(f, x)
    return f

def nil():
    return T0Mpair(T0Mint(-1), T0Mint(-1))

def conflict():
    """conflict board distance column: traverses a reverse board list."""
    b, d, c = T0Mvar("board"), T0Mvar("distance"), T0Mvar("column")
    head = T0Mpfst(b)
    recurse = app(T0Mvar("conflict"), T0Mpsnd(b), T0Mop2("+", d, T0Mint(1)), c)
    diagonal2 = T0Mif0(T0Mop2("==", T0Mop2("-", head, c), d), T0Mbtf(True), recurse)
    diagonal1 = T0Mif0(T0Mop2("==", T0Mop2("-", c, head), d), T0Mbtf(True), diagonal2)
    same_column = T0Mif0(T0Mop2("==", head, c), T0Mbtf(True), diagonal1)
    body = T0Mif0(T0Mop2("==", head, T0Mint(-1)), T0Mbtf(False), same_column)
    return T0Mfix("conflict", "board", T0Mlam("distance", T0Mlam("column", body)))

def build_closed_term(size):
    """Build a closed AST; Python builds/decodes it but never searches."""
    if size < 0:
        raise ValueError("board size must be non-negative")
    board, row, col = T0Mvar("board"), T0Mvar("row"), T0Mvar("column")
    next_col = T0Mop2("+", col, T0Mint(1))
    attacks = app(conflict(), board, T0Mint(1), col)
    next_try = app(T0Mvar("try_column"), next_col)
    extend = app(T0Mvar("search"), T0Mpair(col, board), T0Mop2("+", row, T0Mint(1)))
    choices_body = T0Mif0(T0Mop2("==", col, T0Mint(size)), T0Mint(0), T0Mif0(attacks, next_try, T0Mop2("+", extend, next_try)))
    choices = T0Mfix("try_column", "column", choices_body)
    search_body = T0Mif0(T0Mop2("==", row, T0Mint(size)), T0Mint(1), T0Mapp(choices, T0Mint(0)))
    search = T0Mfix("search", "board", T0Mlam("row", search_body))
    return app(search, nil(), T0Mint(0))

def count_solutions(size):
    result = t0erm_cbv_evaluate0(build_closed_term(size))
    if not isinstance(result, T0Mint):
        raise TypeError("queens result is not an integer")
    return result.arg1

def make_board(size, values):
    if len(values) != size:
        raise ValueError(f"expected {size} entries")
    return list(values)

def board_is_safe(board, row, col):
    return all(r == row or (v != col and abs(r-row) != abs(v-col)) for r, v in enumerate(board))

if __name__ == "__main__":
    print(count_solutions(8))
