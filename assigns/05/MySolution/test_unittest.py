import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from solution import *


class PrettyPrintTests(unittest.TestCase):
    def test_every_constructor_and_literals(self):
        cases = [
            (D0Eint(-999999999999999999), "-999999999999999999"), (D0Ebtf(True), "true"),
            (D0Ebtf(False), "false"), (D0Evar("x"), "x"), (D0Eop1("-1", D0Evar("x")), "(-1 x)"),
            (D0Eop2("+", D0Eint(1), D0Eint(2)), "(1 + 2)"), (D0Elam("x", D0Evar("x")), "(lam x. x)"),
            (D0Efix("f", "n", D0Eapp(D0Evar("f"), D0Evar("n"))), "(fix f(n). (f n))"),
            (D0Eapp(D0Evar("f"), D0Eint(4)), "(f 4)"), (D0Eif0(D0Ebtf(True), D0Eint(1), D0Eint(0)), "(if true then 1 else 0)"),
            (D0Elet("x", D0Eint(1), D0Evar("x")), "(let x = 1 in x)"), (D0Epair(D0Eint(1), D0Eint(2)), "(pair 1 2)"),
            (D0Epfst(D0Evar("p")), "(fst p)"), (D0Epsnd(D0Evar("p")), "(snd p)"),
        ]
        for term, expected in cases: self.assertEqual(d0exp_pretty(term), expected)

    def test_nested_and_not_evaluated(self):
        term = D0Eapp(D0Elam("x", D0Eop2("+", D0Evar("x"), D0Eint(1))), D0Eop2("/", D0Eint(1), D0Eint(0)))
        self.assertEqual(d0exp_pretty(term), "((lam x. (x + 1)) (1 / 0))")


class SubstitutionTests(unittest.TestCase):
    def check(self, term, var, replacement, expected):
        before_term, before_replacement = copy.deepcopy(term), copy.deepcopy(replacement)
        result = d0exp_substitute(term, var, replacement)
        self.assertEqual(d0exp_pretty(result), expected)
        self.assertEqual(term, before_term); self.assertEqual(replacement, before_replacement)
        self.assertEqual(d0exp_pretty(result), d0exp_pretty(d0exp_substitute(term, var, replacement)))
        return result

    def test_all_nonbinding_forms_and_self_replacement(self):
        term = D0Epair(D0Eop1("+1", D0Evar("x")), D0Eif0(D0Evar("x"), D0Epfst(D0Evar("x")), D0Epsnd(D0Eop2("+", D0Evar("z"), D0Evar("x")))))
        self.check(term, "x", D0Eop2("+", D0Evar("x"), D0Eint(1)), "(pair (+1 (x + 1)) (if (x + 1) then (fst (x + 1)) else (snd (z + (x + 1)))))")
        self.check(D0Evar("z"), "x", D0Eint(3), "z")

    def test_shadowing_capture_and_let_initializer(self):
        self.check(D0Elam("x", D0Eop2("+", D0Evar("x"), D0Evar("y"))), "x", D0Eint(3), "(lam x. (x + y))")
        self.check(D0Elam("y", D0Eop2("+", D0Evar("x"), D0Evar("y"))), "x", D0Evar("y"), "(lam y_1. (y + y_1))")
        self.check(D0Elet("x", D0Evar("x"), D0Eop2("+", D0Evar("x"), D0Evar("y"))), "x", D0Eint(3), "(let x = 3 in (x + y))")
        self.check(D0Elet("y", D0Evar("x"), D0Eop2("+", D0Evar("x"), D0Evar("y"))), "x", D0Evar("y"), "(let y_1 = y in (y + y_1))")

    def test_fix_binders_shadow_and_avoid_capture(self):
        self.check(D0Efix("f", "n", D0Eop2("+", D0Evar("x"), D0Eapp(D0Evar("f"), D0Evar("n")))), "x", D0Evar("f"), "(fix f_1(n). (f + (f_1 n)))")
        self.check(D0Efix("f", "n", D0Eop2("+", D0Evar("x"), D0Eapp(D0Evar("f"), D0Evar("n")))), "x", D0Epair(D0Evar("f"), D0Evar("n")), "(fix f_1(n_2). ((pair f n) + (f_1 n_2)))")
        self.check(D0Efix("x", "n", D0Evar("x")), "x", D0Eint(1), "(fix x(n). x)")
        self.check(D0Efix("f", "x", D0Evar("x")), "x", D0Eint(1), "(fix f(x). x)")
        self.check(D0Efix("x", "x", D0Evar("x")), "x", D0Eint(1), "(fix x(x). x)")

    def test_nested_shadowing_fresh_collisions_and_free_variables(self):
        term = D0Elam("y", D0Elam("y", D0Eop2("+", D0Evar("x"), D0Evar("y"))))
        self.check(term, "x", D0Evar("y"), "(lam y_1. (lam y_2. (y + y_2)))")
        term = D0Elam("y", D0Elam("y_1", D0Elet("y", D0Evar("x"), D0Evar("x"))))
        result = self.check(term, "x", D0Evar("y"), "(lam y_2. (lam y_1. (let y_3 = y in y)))")
        self.assertEqual(d0exp_fvset(result), {"y"})
        source = D0Eop2("+", D0Evar("x"), D0Evar("z")); repl = D0Evar("y")
        self.assertEqual(d0exp_fvset(d0exp_substitute(source, "x", repl)), (d0exp_fvset(source) - {"x"}) | d0exp_fvset(repl))
        untouched = D0Elam("x", D0Evar("x"))
        self.assertEqual(d0exp_fvset(d0exp_substitute(untouched, "q", D0Evar("y"))), d0exp_fvset(untouched))


if __name__ == "__main__": unittest.main()
