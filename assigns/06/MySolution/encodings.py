from __future__ import annotations

from target import App, Lam, Var

TRUE = Lam("t0", Lam("f0", Var("t0")))
FALSE = Lam("t0", Lam("f0", Var("f0")))
I = Lam("w0", Var("w0"))

# Z = λg. (λx. g (λv. x x v)) (λx. g (λv. x x v))
Z = Lam(
    "g0",
    App(
        Lam(
            "x0",
            App(Var("g0"), Lam("v0", App(App(Var("x0"), Var("x0")), Var("v0")))),
        ),
        Lam(
            "x0",
            App(Var("g0"), Lam("v0", App(App(Var("x0"), Var("x0")), Var("v0")))),
        ),
    ),
)

PAIR = Lam("a0", Lam("b0", Lam("p0", App(App(Var("p0"), Var("a0")), Var("b0")))))
FST = Lam("p0", App(Var("p0"), TRUE))
SND = Lam("p0", App(Var("p0"), FALSE))


def NUM(n: int):
    if n < 0:
        raise ValueError("Church numerals require n >= 0")
    body = Var("z0")
    for _ in range(n):
        body = App(Var("s0"), body)
    return Lam("s0", Lam("z0", body))


ZERO = NUM(0)
SUCC = Lam(
    "n0",
    Lam(
        "s0",
        Lam(
            "z0",
            App(
                Var("s0"),
                App(App(Var("n0"), Var("s0")), Var("z0")),
            ),
        ),
    ),
)

# Kleene predecessor.  The two continuations carry a one-step delay, so
# applying it to zero reaches ``z0`` and applying it to n+1 reaches n steps.
PRED = Lam(
    "n0", Lam("s0", Lam("z0",
        App(
            App(
                App(Var("n0"),
                    Lam("g0", Lam("h0", App(Var("h0"), App(Var("g0"), Var("s0"))))),
                ),
                Lam("u0", Var("z0")),
            ),
            Lam("u1", Var("u1")),
        ),
    )),
)

ADD = Lam(
    "m0",
    Lam(
        "n0",
        Lam(
            "s0",
            Lam("z0", App(App(Var("m0"), Var("s0")), App(App(Var("n0"), Var("s0")), Var("z0")))),
        ),
    ),
)
MUL = Lam(
    "m0",
    Lam(
        "n0",
        Lam("s0", Lam("z0", App(App(Var("m0"), App(Var("n0"), Var("s0"))), Var("z0")))),
    ),
)
SUB = Lam("m0", Lam("n0", App(App(Var("n0"), PRED), Var("m0"))))

NOT = Lam("b0", App(App(Var("b0"), FALSE), TRUE))
AND = Lam("p0", Lam("q0", App(App(Var("p0"), Var("q0")), FALSE)))
OR = Lam("p0", Lam("q0", App(App(Var("p0"), TRUE), Var("q0"))))
ISZERO = Lam("n0", App(App(Var("n0"), Lam("_0", FALSE)), TRUE))

# Comparisons are expressed through truncated subtraction.  ``n - m`` is
# zero exactly when n <= m, hence m < n iff it is *not* zero.
LT = Lam("m0", Lam("n0", App(NOT, App(ISZERO, App(App(SUB, Var("n0")), Var("m0"))))))
LE = Lam("m0", Lam("n0", App(ISZERO, App(App(SUB, Var("m0")), Var("n0")))))
GT = Lam("m0", Lam("n0", App(App(LT, Var("n0")), Var("m0"))))
GE = Lam("m0", Lam("n0", App(NOT, App(App(LT, Var("m0")), Var("n0")))))
EQ = Lam(
    "m0",
    Lam(
        "n0",
        App(
            App(AND, App(NOT, App(App(LT, Var("m0")), Var("n0")))),
            App(NOT, App(App(LT, Var("n0")), Var("m0"))),
        ),
    ),
)
NEQ = Lam("m0", Lam("n0", App(NOT, App(App(EQ, Var("m0")), Var("n0")))))

__all__ = [
    "TRUE",
    "FALSE",
    "I",
    "Z",
    "PAIR",
    "FST",
    "SND",
    "NUM",
    "ZERO",
    "SUCC",
    "PRED",
    "ADD",
    "MUL",
    "SUB",
    "NOT",
    "AND",
    "OR",
    "ISZERO",
    "LT",
    "LE",
    "GT",
    "GE",
    "EQ",
    "NEQ",
]
