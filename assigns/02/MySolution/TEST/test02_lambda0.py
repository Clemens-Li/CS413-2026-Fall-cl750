import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lambda0 import (
    T0Mint,
    T0Mbtf,
    T0Mlam,
    T0Mvar,
    T0Mapp,
    T0Mop2,
    T0Mpair,
    T0Mpfst,
    T0Mpsnd,
    T0Mfix,
    t0erm_size,
    t0erm_fvset,
    t0erm_subst0,
    t0erm_cbv_evaluate0,
)


class TestPairOperations(unittest.TestCase):
    def test_size_and_fvset(self):
        self.assertEqual(t0erm_size(T0Mpair(T0Mint(1), T0Mint(2))), 3)
        self.assertEqual(
            t0erm_fvset(T0Mpfst(T0Mpair(T0Mvar("x"), T0Mvar("y")))),
            frozenset({"x", "y"}),
        )
        term = T0Mpair(
            T0Mlam("x", T0Mpair(T0Mvar("x"), T0Mvar("z"))),
            T0Mpfst(T0Mpair(T0Mvar("y"), T0Mvar("w"))),
        )
        self.assertEqual(t0erm_size(term), 9)
        self.assertEqual(t0erm_fvset(term), frozenset({"y", "w", "z"}))

    def test_substitution_in_pair_and_projection(self):
        term = T0Mpair(T0Mvar("x"), T0Mpfst(T0Mpair(T0Mvar("x"), T0Mvar("y"))))
        substituted = t0erm_subst0(term, "x", T0Mint(7))
        self.assertEqual(substituted, T0Mpair(T0Mint(7), T0Mpfst(T0Mpair(T0Mint(7), T0Mvar("y")))))

        nested = T0Mlam("x", T0Mpair(T0Mvar("x"), T0Mpfst(T0Mpair(T0Mvar("x"), T0Mvar("y")))))
        self.assertEqual(
            t0erm_subst0(nested, "y", T0Mint(5)),
            T0Mlam("x", T0Mpair(T0Mvar("x"), T0Mpfst(T0Mpair(T0Mvar("x"), T0Mint(5))))),
        )

        f = T0Mfix("f", "x", T0Mpair(T0Mvar("x"), T0Mapp(T0Mvar("f"), T0Mvar("x"))))
        self.assertEqual(t0erm_subst0(f, "x", T0Mint(9)), f)

    def test_cbv_pair_and_projections(self):
        term = T0Mpfst(T0Mpair(T0Mint(1), T0Mop2("+", T0Mint(2), T0Mint(3))))
        self.assertEqual(t0erm_cbv_evaluate0(term), T0Mint(1))
        term = T0Mpsnd(T0Mpair(T0Mint(1), T0Mop2("+", T0Mint(2), T0Mint(3))))
        self.assertEqual(t0erm_cbv_evaluate0(term), T0Mint(5))

        pair_value = T0Mpair(T0Mlam("x", T0Mvar("x")), T0Mint(7))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mpfst(pair_value)), T0Mlam("x", T0Mvar("x")))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mpsnd(pair_value)), T0Mint(7))

        with self.assertRaises(TypeError):
            t0erm_cbv_evaluate0(T0Mpfst(T0Mint(1)))
        with self.assertRaises(TypeError):
            t0erm_cbv_evaluate0(T0Mpsnd(T0Mbtf(True)))

    def test_left_to_right_evaluation(self):
        term = T0Mpfst(T0Mpair(T0Mop2("/", T0Mint(1), T0Mint(0)), T0Mint(2)))
        with self.assertRaises(ZeroDivisionError):
            t0erm_cbv_evaluate0(term)

        term = T0Mpsnd(T0Mpair(T0Mint(1), T0Mop2("/", T0Mint(1), T0Mint(0))))
        with self.assertRaises(ZeroDivisionError):
            t0erm_cbv_evaluate0(term)

    def test_function_accepts_and_returns_pairs(self):
        maker = T0Mlam("p", T0Mpair(T0Mpfst(T0Mvar("p")), T0Mop2("+", T0Mpsnd(T0Mvar("p")), T0Mint(1))))
        value = T0Mpair(T0Mint(2), T0Mint(3))
        result = t0erm_cbv_evaluate0(T0Mapp(maker, value))
        self.assertEqual(result, T0Mpair(T0Mint(2), T0Mint(4)))

        chooser = T0Mlam("p", T0Mpsnd(T0Mvar("p")))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mapp(chooser, T0Mpair(T0Mint(5), T0Mlam("x", T0Mvar("x"))))), T0Mlam("x", T0Mvar("x")))


if __name__ == "__main__":
    unittest.main()
