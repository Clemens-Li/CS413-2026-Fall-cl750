"""Independent pytest-style tests; these do not use unittest.TestCase."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from solution import *


def test_pretty_printing_all_forms_and_no_evaluation():
    term = D0Elet("x", D0Epair(D0Eint(-2), D0Ebtf(False)), D0Eif0(D0Ebtf(True), D0Efix("f", "n", D0Eapp(D0Evar("f"), D0Evar("n"))), D0Epsnd(D0Epfst(D0Eop2("/", D0Eint(1), D0Eint(0))))))
    assert d0exp_pretty(term) == "(let x = (pair -2 false) in (if true then (fix f(n). (f n)) else (snd (fst (1 / 0)))))"
    assert d0exp_pretty(D0Eop1("-1", D0Evar("a"))) == "(-1 a)"


def test_substitution_forms_and_inputs_unchanged():
    term = D0Eapp(D0Eop2("+", D0Evar("x"), D0Evar("q")), D0Epair(D0Epfst(D0Evar("x")), D0Epsnd(D0Evar("x"))))
    original, replacement = copy.deepcopy(term), D0Eint(99)
    assert d0exp_pretty(d0exp_substitute(term, "x", replacement)) == "((99 + q) (pair (fst 99) (snd 99)))"
    assert term == original and replacement == D0Eint(99)


def test_capture_avoidance_lambda_let_fix_and_shadowing():
    assert d0exp_pretty(d0exp_substitute(D0Elam("a", D0Evar("x")), "x", D0Evar("a"))) == "(lam a_1. a)"
    assert d0exp_pretty(d0exp_substitute(D0Elet("a", D0Evar("x"), D0Evar("x")), "x", D0Evar("a"))) == "(let a_1 = a in a)"
    fix = D0Efix("f", "n", D0Eop2("+", D0Evar("x"), D0Eapp(D0Evar("f"), D0Evar("n"))))
    assert d0exp_pretty(d0exp_substitute(fix, "x", D0Epair(D0Evar("f"), D0Evar("n")))) == "(fix f_1(n_2). ((pair f n) + (f_1 n_2)))"
    assert d0exp_pretty(d0exp_substitute(D0Efix("p", "p", D0Evar("x")), "x", D0Evar("p"))) == "(fix p(p_1). p)"


def test_nested_shadowing_determinism_and_free_variable_law():
    term = D0Elam("y", D0Elam("y_1", D0Eop2("+", D0Evar("x"), D0Evar("y"))))
    one = d0exp_substitute(term, "x", D0Evar("y")); two = d0exp_substitute(term, "x", D0Evar("y"))
    assert d0exp_pretty(one) == "(lam y_2. (lam y_1. (y + y_2)))"
    assert d0exp_pretty(one) == d0exp_pretty(two)
    source = D0Elet("a", D0Evar("x"), D0Eop2("+", D0Evar("x"), D0Evar("z")))
    result = d0exp_substitute(source, "x", D0Evar("y"))
    assert d0exp_fvset(result) == (d0exp_fvset(source) - {"x"}) | {"y"}
