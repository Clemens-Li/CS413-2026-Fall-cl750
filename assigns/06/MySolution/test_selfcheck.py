from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ast = load("lambda1_vp", ROOT.parent.parent / "05" / "lambda1_vp.py")
target = load("target", ROOT / "target.py")
encodings = load("church_encodings", ROOT / "church_encodings.py")
compiler = load("compiler", ROOT / "compiler.py")
observers = load("observers", ROOT / "observers.py")
evaluator = load("evaluator", ROOT / "evaluator.py")
A = ast


def loop():
    return A.D0Eapp(A.D0Efix("loop", "x", A.D0Eapp(A.D0Evar("loop"), A.D0Evar("x"))), A.D0Eint(0))


def fact(n):
    body = A.D0Eif0(
        A.D0Eop2("==", A.D0Evar("n"), A.D0Eint(0)),
        A.D0Eint(1),
        A.D0Eop2("*", A.D0Evar("n"), A.D0Eapp(A.D0Evar("fact"), A.D0Eop2("-", A.D0Evar("n"), A.D0Eint(1)))),
    )
    return A.D0Eapp(A.D0Efix("fact", "n", body), A.D0Eint(n))


def fib(n):
    body = A.D0Eif0(
        A.D0Eop2("<=", A.D0Evar("n"), A.D0Eint(1)),
        A.D0Evar("n"),
        A.D0Eop2(
            "+",
            A.D0Eapp(A.D0Evar("fib"), A.D0Eop2("-", A.D0Evar("n"), A.D0Eint(1))),
            A.D0Eapp(A.D0Evar("fib"), A.D0Eop2("-", A.D0Evar("n"), A.D0Eint(2))),
        ),
    )
    return A.D0Eapp(A.D0Efix("fib", "n", body), A.D0Eint(n))


def reduce(expr, budget=100_000):
    return target.eval_target(compiler.compile_expr(expr), budget)


def nat(expr, budget=100_000):
    result = reduce(expr, budget)
    if result.status == "exhausted":
        return None
    value, _, status = observers.observe_nat(result.value, budget)
    return None if status == "exhausted" else value


def boolean(expr, budget=100_000):
    result = reduce(expr, budget)
    if result.status == "exhausted":
        return None
    value, _, status = observers.observe_bool(result.value, budget)
    return None if status == "exhausted" else value


def only_target(term):
    if isinstance(term, target.Var):
        return True
    if isinstance(term, target.Lam):
        return only_target(term.body)
    if isinstance(term, target.App):
        return only_target(term.fn) and only_target(term.arg)
    return False


class SubstitutionAndReductionTests(unittest.TestCase):
    def test_capture_avoiding_substitution(self):
        original = target.Lam("y", target.Var("x"))
        replacement = target.Var("y")
        answer = target.substitute(original, "x", replacement)
        self.assertNotEqual(answer.name, "y")
        self.assertEqual(answer.body, target.Var("y"))
        self.assertEqual(target.free_vars(answer), {"y"})
        self.assertEqual(original, target.Lam("y", target.Var("x")))
        self.assertEqual(replacement, target.Var("y"))

    def test_shadowing_stops_substitution(self):
        term = target.Lam("x", target.Var("x"))
        self.assertEqual(target.substitute(term, "x", target.Var("y")), term)

    def test_capture_avoidance_renames_bound_occurrences(self):
        # [x := y] (lam y. x y) must be alpha-equivalent to (lam fresh. y fresh):
        # the bound y is renamed together with its binder; the inserted y stays free.
        original = target.Lam("y", target.App(target.Var("x"), target.Var("y")))
        replacement = target.Var("y")
        answer = target.substitute(original, "x", replacement)
        self.assertIsInstance(answer, target.Lam)
        fresh = answer.name
        self.assertNotEqual(fresh, "y")
        self.assertEqual(answer.body, target.App(target.Var("y"), target.Var(fresh)))
        self.assertEqual(target.free_vars(answer), {"y"})
        self.assertEqual(original, target.Lam("y", target.App(target.Var("x"), target.Var("y"))))

    def test_capture_avoidance_respects_inner_shadowing_and_fresh_names(self):
        # The inner (lam y. y) rebinds y, so it must be left alone by the renaming.
        original = target.Lam(
            "y",
            target.App(target.Var("x"), target.App(target.Var("y"), target.Lam("y", target.Var("y")))),
        )
        answer = target.substitute(original, "x", target.Var("y"))
        fresh = answer.name
        self.assertNotEqual(fresh, "y")
        self.assertEqual(
            answer.body,
            target.App(target.Var("y"), target.App(target.Var(fresh), target.Lam("y", target.Var("y")))),
        )
        self.assertEqual(target.free_vars(answer), {"y"})
        # The fresh name must also avoid names already used in the body (y_1 here).
        crowded = target.Lam("y", target.App(target.Var("x"), target.App(target.Var("y"), target.Var("y_1"))))
        answer = target.substitute(crowded, "x", target.Var("y"))
        self.assertNotIn(answer.name, {"y", "y_1"})
        self.assertEqual(target.free_vars(answer), {"y", "y_1"})

    def test_cbv_order_zero_steps_determinism_and_exhaustion(self):
        identity = target.Lam("x", target.Var("x"))
        under_lambda = target.Lam("x", target.App(target.Lam("y", target.Var("y")), target.Lam("z", target.Var("z"))))
        self.assertEqual(target.eval_target(under_lambda, 0).status, "complete")
        self.assertEqual(target.eval_target(under_lambda, 0).steps, 0)
        self.assertEqual(target.eval_target(identity, 0).status, "complete")
        self.assertEqual(target.eval_target(identity, 0).steps, 0)

        apply_id = target.App(identity, identity)
        zero = target.eval_target(apply_id, 0)
        one = target.eval_target(apply_id, 1)
        self.assertEqual(zero.status, "exhausted")
        self.assertEqual(zero.steps, 0)
        self.assertEqual(one.status, "complete")
        self.assertEqual(one.steps, 1)

        nested = target.App(apply_id, apply_id)
        first = target.eval_target(nested, 10)
        second = target.eval_target(nested, 10)
        self.assertEqual((first.status, first.steps), (second.status, second.steps))
        self.assertEqual(nested, target.App(apply_id, apply_id))

        omega = target.Lam("x", target.App(target.Var("x"), target.Var("x")))
        diverging = target.App(omega, omega)
        snapshot = copy.deepcopy(diverging)
        exhausted = target.eval_target(diverging, 12)
        self.assertEqual(exhausted.status, "exhausted")
        self.assertEqual(exhausted.steps, 12)
        self.assertEqual(diverging, snapshot)

    def test_function_then_argument_evaluation_order(self):
        identity = target.Lam("x", target.Var("x"))
        apply_id = target.App(identity, identity)
        omega = target.Lam("x", target.App(target.Var("x"), target.Var("x")))
        diverging = target.App(omega, omega)

        # (I I) (I I): left child, then right child, then the outer contraction.
        done = target.eval_target(target.App(apply_id, apply_id), 10)
        self.assertEqual((done.status, done.steps, done.value), ("complete", 3, identity))

        # Diverging function position: the argument must still be untouched.
        fn_first = target.eval_target(target.App(diverging, apply_id), 8)
        self.assertEqual((fn_first.status, fn_first.steps), ("exhausted", 8))
        self.assertEqual(fn_first.value.arg, apply_id)

        # Diverging argument: the function position must already be a value (I I -> I).
        arg_second = target.eval_target(target.App(apply_id, diverging), 8)
        self.assertEqual((arg_second.status, arg_second.steps), ("exhausted", 8))
        self.assertEqual(arg_second.value.fn, identity)

    def test_printer(self):
        self.assertEqual(target.pretty_term(target.Var("x")), "x")
        self.assertEqual(target.pretty_term(target.Lam("x", target.Var("x"))), "(lam x. x)")
        self.assertEqual(
            target.pretty_term(target.App(target.Lam("x", target.Var("x")), target.Var("y"))),
            "((lam x. x) y)",
        )


class EncodingTests(unittest.TestCase):
    def observe_nat(self, term, budget=10_000):
        value, _, status = observers.observe_nat(term, budget)
        self.assertEqual(status, "complete")
        return value

    def observe_bool(self, term, budget=10_000):
        value, _, status = observers.observe_bool(term, budget)
        self.assertEqual(status, "complete")
        return value

    def test_library_is_closed(self):
        for name in encodings.__all__:
            if name == "NUM":
                self.assertEqual(target.free_vars(encodings.NUM(3)), set())
                continue
            self.assertEqual(target.free_vars(getattr(encodings, name)), set(), name)

    def test_numerals_predecessor_and_arithmetic(self):
        self.assertEqual(self.observe_nat(encodings.NUM(0)), 0)
        self.assertEqual(self.observe_nat(target.App(encodings.PRED, encodings.NUM(0))), 0)
        self.assertEqual(self.observe_nat(target.App(encodings.PRED, encodings.NUM(1))), 0)
        self.assertEqual(self.observe_nat(target.App(encodings.SUCC, encodings.NUM(2))), 3)
        self.assertEqual(self.observe_nat(target.App(target.App(encodings.ADD, encodings.NUM(2)), encodings.NUM(3))), 5)
        self.assertEqual(self.observe_nat(target.App(target.App(encodings.MUL, encodings.NUM(3)), encodings.NUM(4))), 12)
        self.assertEqual(self.observe_nat(target.App(target.App(encodings.SUB, encodings.NUM(2)), encodings.NUM(5))), 0)
        self.assertEqual(self.observe_nat(target.App(target.App(encodings.SUB, encodings.NUM(5)), encodings.NUM(2))), 3)

    def test_comparisons_and_booleans(self):
        self.assertTrue(self.observe_bool(encodings.TRUE))
        self.assertFalse(self.observe_bool(encodings.FALSE))
        self.assertEqual(self.observe_nat(encodings.FALSE), 0)
        self.assertFalse(self.observe_bool(encodings.NUM(0)))
        for op, left, right, want in (
            ("LT", 2, 3, True),
            ("LT", 3, 2, False),
            ("LT", 2, 2, False),
            ("LE", 2, 3, True),
            ("LE", 3, 2, False),
            ("LE", 2, 2, True),
            ("GT", 3, 2, True),
            ("GT", 2, 3, False),
            ("GE", 3, 2, True),
            ("GE", 2, 3, False),
            ("EQ", 4, 4, True),
            ("EQ", 4, 5, False),
            ("NEQ", 4, 5, True),
            ("NEQ", 4, 4, False),
        ):
            term = target.App(target.App(getattr(encodings, op), encodings.NUM(left)), encodings.NUM(right))
            self.assertEqual(self.observe_bool(term), want, f"{op} {left} {right}")

        for p, q, want_and, want_or in (
            (True, True, True, True),
            (True, False, False, True),
            (False, True, False, True),
            (False, False, False, False),
        ):
            left = encodings.TRUE if p else encodings.FALSE
            right = encodings.TRUE if q else encodings.FALSE
            self.assertEqual(self.observe_bool(target.App(target.App(encodings.AND, left), right)), want_and)
            self.assertEqual(self.observe_bool(target.App(target.App(encodings.OR, left), right)), want_or)
        self.assertFalse(self.observe_bool(target.App(encodings.NOT, encodings.TRUE)))
        self.assertTrue(self.observe_bool(target.App(encodings.NOT, encodings.FALSE)))

    def test_observation_shapes_and_exhaustion(self):
        renamed_true = target.Lam("then", target.Lam("else_", target.Var("then")))
        self.assertTrue(self.observe_bool(renamed_true))
        value, steps, status = observers.observe_nat(encodings.NUM(2), 0)
        self.assertEqual(status, "exhausted")
        self.assertIsNone(value)
        self.assertEqual(steps, 0)
        with self.assertRaises(ValueError):
            observers.observe_bool(target.Lam("x", target.Var("y")), 10)
        with self.assertRaises(ValueError):
            target.eval_target(target.Var("free"), 10)


class CompilerCoverageTests(unittest.TestCase):
    def test_every_constructor_and_operator(self):
        self.assertEqual(nat(A.D0Eint(0)), 0)
        self.assertTrue(boolean(A.D0Ebtf(True)))
        self.assertFalse(boolean(A.D0Ebtf(False)))
        self.assertEqual(nat(A.D0Eop2("+", A.D0Eint(2), A.D0Eop2("*", A.D0Eint(3), A.D0Eint(4)))), 14)
        self.assertEqual(nat(A.D0Eop2("-", A.D0Eint(2), A.D0Eint(5))), 0)
        self.assertFalse(boolean(A.D0Eop1("not", A.D0Ebtf(True))))
        self.assertTrue(boolean(A.D0Eop1("not", A.D0Ebtf(False))))
        cases = {
            "<": (True, False, False),
            "<=": (True, False, True),
            ">": (False, True, False),
            ">=": (False, True, True),
            "==": (False, False, True),
            "!=": (True, True, False),
        }
        for op, (lt, gt, eq) in cases.items():
            self.assertEqual(boolean(A.D0Eop2(op, A.D0Eint(2), A.D0Eint(3))), lt, op)
            self.assertEqual(boolean(A.D0Eop2(op, A.D0Eint(3), A.D0Eint(2))), gt, op)
            self.assertEqual(boolean(A.D0Eop2(op, A.D0Eint(2), A.D0Eint(2))), eq, op)
        for p in (True, False):
            for q in (True, False):
                self.assertEqual(boolean(A.D0Eop2("and", A.D0Ebtf(p), A.D0Ebtf(q))), p and q)
                self.assertEqual(boolean(A.D0Eop2("or", A.D0Ebtf(p), A.D0Ebtf(q))), p or q)
        self.assertEqual(nat(A.D0Eif0(A.D0Eop2("<=", A.D0Eint(2), A.D0Eint(3)), A.D0Eint(7), A.D0Eint(9))), 7)
        self.assertEqual(
            nat(A.D0Eapp(A.D0Elet("x", A.D0Eint(3), A.D0Elam("y", A.D0Eop2("+", A.D0Evar("x"), A.D0Evar("y")))), A.D0Eint(4))),
            7,
        )
        self.assertEqual(nat(A.D0Epfst(A.D0Epair(A.D0Eint(2), A.D0Ebtf(True)))), 2)
        self.assertTrue(boolean(A.D0Epsnd(A.D0Epair(A.D0Eint(2), A.D0Ebtf(True)))))
        self.assertEqual(
            nat(A.D0Eapp(A.D0Elam("f", A.D0Eapp(A.D0Evar("f"), A.D0Eint(3))), A.D0Elam("x", A.D0Eop2("+", A.D0Evar("x"), A.D0Eint(1))))),
            4,
        )

    def test_scope_open_terms_and_immutability(self):
        nested = A.D0Elet("x", A.D0Eint(1), A.D0Elet("x", A.D0Eop2("+", A.D0Evar("x"), A.D0Eint(1)), A.D0Evar("x")))
        self.assertEqual(nat(nested), 2)
        initializer_scope = A.D0Elet("x", A.D0Evar("x"), A.D0Evar("x"))
        compiled_open = compiler.compile_expr(initializer_scope)
        self.assertEqual(target.free_vars(compiled_open), set(A.d0exp_fvset(initializer_scope)))
        coincident = A.D0Eapp(A.D0Efix("f", "f", A.D0Evar("f")), A.D0Eint(3))
        self.assertEqual(nat(coincident), 3)
        uses_both = A.D0Eapp(
            A.D0Efix(
                "f",
                "x",
                A.D0Eif0(A.D0Eop2("==", A.D0Evar("x"), A.D0Eint(0)), A.D0Eint(1), A.D0Eapp(A.D0Evar("f"), A.D0Eop2("-", A.D0Evar("x"), A.D0Eint(1)))),
            ),
            A.D0Eint(3),
        )
        self.assertEqual(nat(uses_both), 1)
        colliding = A.D0Eop2("+", A.D0Evar("s"), A.D0Eop2("+", A.D0Evar("z"), A.D0Eop2("+", A.D0Evar("t"), A.D0Eop2("+", A.D0Evar("f"), A.D0Evar("x")))))
        compiled = compiler.compile_expr(colliding)
        self.assertEqual(target.free_vars(compiled), {"s", "z", "t", "f", "x"})
        source = A.D0Elet("x", A.D0Eint(3), A.D0Evar("x"))
        before = copy.deepcopy(source)
        compiler.compile_expr(source)
        self.assertEqual(source, before)

    def test_short_circuit_and_strict_divergence(self):
        self.assertEqual(nat(A.D0Eif0(A.D0Ebtf(True), A.D0Eint(1), loop())), 1)
        self.assertEqual(nat(A.D0Eif0(A.D0Ebtf(False), loop(), A.D0Eint(2))), 2)
        self.assertFalse(boolean(A.D0Eop2("and", A.D0Ebtf(False), loop())))
        self.assertTrue(boolean(A.D0Eop2("or", A.D0Ebtf(True), loop())))
        self.assertEqual(reduce(A.D0Eapp(A.D0Elam("x", A.D0Eint(0)), loop()), 200).status, "exhausted")
        self.assertEqual(reduce(A.D0Elet("x", loop(), A.D0Eint(2)), 200).status, "exhausted")
        self.assertEqual(reduce(A.D0Epfst(A.D0Epair(A.D0Eint(2), loop())), 200).status, "exhausted")
        self.assertEqual(reduce(A.D0Epsnd(A.D0Epair(loop(), A.D0Ebtf(True))), 200).status, "exhausted")

    def test_demos_nested_pairs_and_rejection(self):
        self.assertEqual(nat(A.D0Eop2("+", A.D0Eint(2), A.D0Eop2("*", A.D0Eint(3), A.D0Eint(4)))), 14)
        self.assertEqual(nat(fact(4)), 24)
        self.assertEqual(nat(fib(5)), 5)
        self.assertEqual(reduce(loop(), 200).status, "exhausted")
        nested = A.D0Epair(A.D0Epair(A.D0Eint(2), A.D0Ebtf(True)), A.D0Eint(3))
        outcome = reduce(nested, 10_000)
        decoded, _, status = observers.observe_pair(outcome.value, ("nat", "bool"), "nat", 10_000)
        self.assertEqual(status, "complete")
        self.assertEqual(decoded, ((2, True), 3))
        with self.assertRaises(ValueError):
            compiler.compile_expr(A.D0Eif0(A.D0Ebtf(True), A.D0Eint(1), A.D0Eint(-1)))
        with self.assertRaises(ValueError):
            compiler.compile_expr(A.D0Elam("x", A.D0Eop2("/", A.D0Eint(4), A.D0Eint(2))))
        with self.assertRaises(ValueError):
            compiler.compile_expr(A.D0Eop1("neg", A.D0Eint(1)))

    def test_selected_branch_divergence(self):
        self.assertEqual(reduce(A.D0Eif0(A.D0Ebtf(True), loop(), A.D0Eint(1)), 200).status, "exhausted")
        self.assertEqual(reduce(A.D0Eif0(A.D0Ebtf(False), A.D0Eint(1), loop()), 200).status, "exhausted")
        self.assertEqual(reduce(A.D0Eop2("and", A.D0Ebtf(True), loop()), 200).status, "exhausted")
        self.assertEqual(reduce(A.D0Eop2("or", A.D0Ebtf(False), loop()), 200).status, "exhausted")

    def test_generated_binders_do_not_capture_source_names(self):
        # Source variables named like compiler-introduced binders (u, v, f_1, x_1, ...).
        free_u_v = A.D0Eif0(A.D0Evar("c"), A.D0Evar("u"), A.D0Evar("v"))
        self.assertEqual(target.free_vars(compiler.compile_expr(free_u_v)), {"c", "u", "v"})
        short = A.D0Eop2("and", A.D0Evar("u"), A.D0Eop2("or", A.D0Evar("v"), A.D0Evar("w")))
        self.assertEqual(target.free_vars(compiler.compile_expr(short)), {"u", "v", "w"})
        fix_open = A.D0Efix(
            "f", "x",
            A.D0Eop2("+", A.D0Eapp(A.D0Evar("f"), A.D0Evar("x")), A.D0Eop2("+", A.D0Evar("f_1"), A.D0Evar("x_1"))),
        )
        self.assertEqual(target.free_vars(compiler.compile_expr(fix_open)), {"f_1", "x_1"})
        # Closed programs whose source names collide with generated ones still run correctly.
        for cond, expected in ((True, 2), (False, 3)):
            program = A.D0Elet(
                "u", A.D0Eint(2),
                A.D0Elet("v", A.D0Eint(3), A.D0Eif0(A.D0Ebtf(cond), A.D0Evar("u"), A.D0Evar("v"))),
            )
            self.assertEqual(nat(program), expected)
        collide_fix = A.D0Elet(
            "f_1", A.D0Eint(5),
            A.D0Elet(
                "x_1", A.D0Eint(1),
                A.D0Eapp(
                    A.D0Efix("f", "x", A.D0Eop2("+", A.D0Evar("x"), A.D0Eop2("+", A.D0Evar("f_1"), A.D0Evar("x_1")))),
                    A.D0Eint(2),
                ),
            ),
        )
        self.assertEqual(nat(collide_fix), 8)
        # Each fix binder is available independently of the other.
        param_only = A.D0Eapp(A.D0Efix("f", "x", A.D0Evar("x")), A.D0Eint(4))
        self.assertEqual(nat(param_only), 4)

    def test_compiled_results_agree_with_shared_source_evaluator(self):
        programs = [
            (A.D0Eop2("+", A.D0Eint(2), A.D0Eop2("*", A.D0Eint(3), A.D0Eint(4))), "nat"),
            (A.D0Eop2("-", A.D0Eint(2), A.D0Eint(5)), "nat"),
            (A.D0Eop2("-", A.D0Eint(9), A.D0Eint(4)), "nat"),
            (A.D0Eif0(A.D0Eop2("<=", A.D0Eint(2), A.D0Eint(3)), A.D0Eint(7), A.D0Eint(9)), "nat"),
            (A.D0Elet("x", A.D0Eint(3), A.D0Eapp(A.D0Elam("y", A.D0Eop2("+", A.D0Evar("x"), A.D0Evar("y"))), A.D0Eint(4))), "nat"),
            (A.D0Epfst(A.D0Epair(A.D0Eint(2), A.D0Ebtf(True))), "nat"),
            (A.D0Epsnd(A.D0Epair(A.D0Eint(2), A.D0Ebtf(True))), "bool"),
            (A.D0Eop2("and", A.D0Ebtf(True), A.D0Ebtf(False)), "bool"),
            (A.D0Eop2("or", A.D0Ebtf(False), A.D0Ebtf(True)), "bool"),
            (A.D0Eop2("and", A.D0Ebtf(False), loop()), "bool"),
            (A.D0Eop2("!=", A.D0Eint(4), A.D0Eint(4)), "bool"),
            (A.D0Eop1("not", A.D0Eop2(">=", A.D0Eint(1), A.D0Eint(2))), "bool"),
            (fact(4), "nat"),
            (fib(5), "nat"),
        ]
        for source, kind in programs:
            expected = evaluator.evaluate(source)
            observed = nat(source) if kind == "nat" else boolean(source)
            self.assertEqual(observed, expected, repr(source))
            self.assertIs(type(observed), type(expected), repr(source))

    def test_purity_and_no_evaluator_during_compile(self):
        source = A.D0Eop2("+", A.D0Eint(2), A.D0Eop2("*", A.D0Eint(3), A.D0Eint(4)))
        compiled = compiler.compile_expr(source)
        self.assertTrue(only_target(compiled))
        self.assertTrue(only_target(compiler.compile_expr(loop())))
        self.assertIsInstance(compiler.CompileVisitor({}, set()), ast.D0ExpVisitor)

        def boom(*_args, **_kwargs):
            raise AssertionError("shared evaluator used during compilation")

        original_eval = evaluator.evaluate
        original_target = target.eval_target
        evaluator.evaluate = boom
        target.eval_target = boom
        try:
            compiler.compile_expr(source)
            compiler.compile_expr(loop())
        finally:
            evaluator.evaluate = original_eval
            target.eval_target = original_target
        self.assertEqual(evaluator.evaluate(A.D0Eop2("-", A.D0Eint(2), A.D0Eint(5))), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
