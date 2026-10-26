"""Run every required end-to-end demonstration from the Assignment 6 brief."""
from __future__ import annotations
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

A = load("lambda1_vp", ROOT.parent.parent / "05" / "lambda1_vp.py")
T = load("target", ROOT / "target.py")
load("church_encodings", ROOT / "church_encodings.py")
C = load("compiler", ROOT / "compiler.py")
O = load("observers", ROOT / "observers.py")
E = load("evaluator", ROOT / "evaluator.py")

EXECUTION_BUDGET = 200_000
OBSERVATION_BUDGET = 200_000

def loop():
    return A.D0Eapp(A.D0Efix("loop", "x", A.D0Eapp(A.D0Evar("loop"), A.D0Evar("x"))), A.D0Eint(0))

def fact(n):
    body = A.D0Eif0(A.D0Eop2("==", A.D0Evar("n"), A.D0Eint(0)), A.D0Eint(1),
        A.D0Eop2("*", A.D0Evar("n"), A.D0Eapp(A.D0Evar("fact"), A.D0Eop2("-", A.D0Evar("n"), A.D0Eint(1)))))
    return A.D0Eapp(A.D0Efix("fact", "n", body), A.D0Eint(n))

def fib(n):
    body = A.D0Eif0(A.D0Eop2("<=", A.D0Evar("n"), A.D0Eint(1)), A.D0Evar("n"),
        A.D0Eop2("+", A.D0Eapp(A.D0Evar("fib"), A.D0Eop2("-", A.D0Evar("n"), A.D0Eint(1))),
                  A.D0Eapp(A.D0Evar("fib"), A.D0Eop2("-", A.D0Evar("n"), A.D0Eint(2)))))
    return A.D0Eapp(A.D0Efix("fib", "n", body), A.D0Eint(n))

def run(label, source, kind, expected):
    compiled = C.compile_expr(source)
    # Divergence is demonstrated with a deliberately small finite budget;
    # exhaustion is evidence of needing another step, not a nontermination proof.
    execution_budget = 500 if expected == "exhausted" else EXECUTION_BUDGET
    outcome = T.eval_target(compiled, execution_budget)
    decoded = None
    observation = "not run"
    obs_steps = 0
    if outcome.status == "complete":
        if kind == "nat": decoded, obs_steps, observation = O.observe_nat(outcome.value, OBSERVATION_BUDGET)
        elif kind == "bool": decoded, obs_steps, observation = O.observe_bool(outcome.value, OBSERVATION_BUDGET)
        else: decoded, obs_steps, observation = O.observe_pair(outcome.value, *kind, OBSERVATION_BUDGET)
    source_value = "diverges (expected)" if expected == "exhausted" else E.evaluate(source)
    print(f"\n{label}\n  source: {source!r}\n  target: {T.pretty_term(compiled)}\n  execution: {outcome.status}, {outcome.steps}/{execution_budget} beta steps\n  observation: {observation}, {obs_steps}/{OBSERVATION_BUDGET} beta steps\n  source result: {source_value!r}\n  decoded: {decoded!r}; expected: {expected!r}")

if __name__ == "__main__":
    examples = [
        ("arithmetic", A.D0Eop2("+", A.D0Eint(2), A.D0Eop2("*", A.D0Eint(3), A.D0Eint(4))), "nat", 14),
        ("truncated subtraction", A.D0Eop2("-", A.D0Eint(2), A.D0Eint(5)), "nat", 0),
        ("conditional", A.D0Eif0(A.D0Eop2("<=", A.D0Eint(2), A.D0Eint(3)), A.D0Eint(7), A.D0Eint(9)), "nat", 7),
        ("let and closure", A.D0Eapp(A.D0Elet("x", A.D0Eint(3), A.D0Elam("y", A.D0Eop2("+", A.D0Evar("x"), A.D0Evar("y")))), A.D0Eint(4)), "nat", 7),
        ("first pair projection", A.D0Epfst(A.D0Epair(A.D0Eint(2), A.D0Ebtf(True))), "nat", 2),
        ("second pair projection", A.D0Epsnd(A.D0Epair(A.D0Eint(2), A.D0Ebtf(True))), "bool", True),
        ("higher order", A.D0Eapp(A.D0Elam("f", A.D0Eapp(A.D0Evar("f"), A.D0Eint(3))), A.D0Elam("x", A.D0Eop2("+", A.D0Evar("x"), A.D0Eint(1)))), "nat", 4),
        ("and", A.D0Eop2("and", A.D0Ebtf(True), A.D0Ebtf(False)), "bool", False),
        ("or", A.D0Eop2("or", A.D0Ebtf(False), A.D0Ebtf(True)), "bool", True),
        ("unselected loop", A.D0Eif0(A.D0Ebtf(True), A.D0Eint(1), loop()), "nat", 1),
        ("strict function argument", A.D0Eapp(A.D0Elam("x", A.D0Eint(0)), loop()), "nat", "exhausted"),
        ("factorial", fact(4), "nat", 24), ("fibonacci", fib(5), "nat", 5), ("loop", loop(), "nat", "exhausted"),
    ]
    for example in examples: run(*example)
