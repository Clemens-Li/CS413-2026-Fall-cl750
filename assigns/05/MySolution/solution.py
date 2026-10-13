"""Visitor-based pretty printing and capture-avoiding substitution for LAMBDA."""
from __future__ import annotations

from pathlib import Path
import sys

# Permit this module to be imported both from assigns/05 and from MySolution.
SUPPLIED_DIR = str(Path(__file__).resolve().parent.parent)
if SUPPLIED_DIR not in sys.path:
    sys.path.insert(0, SUPPLIED_DIR)

from lambda1_vp import (  # noqa: E402
    D0ExpVisitor, D0Eint, D0Ebtf, D0Eop1, D0Eop2, D0Evar, D0Elam,
    D0Efix, D0Eapp, D0Eif0, D0Elet, D0Epair, D0Epfst, D0Epsnd,
    d0exp, d0exp_fvset,
)


class PrettyPrintVisitor(D0ExpVisitor[str]):
    """Render an expression without evaluating it."""

    def visit_int(self, e): return str(e.arg1)
    def visit_btf(self, e): return "true" if e.arg1 else "false"
    def visit_var(self, e): return e.arg1
    def visit_op1(self, e): return f"({e.name} {e.arg1.accept(self)})"
    def visit_op2(self, e): return f"({e.arg1.accept(self)} {e.name} {e.arg2.accept(self)})"
    def visit_lam(self, e): return f"(lam {e.arg1}. {e.arg2.accept(self)})"
    def visit_fix(self, e): return f"(fix {e.arg1}({e.arg2}). {e.arg3.accept(self)})"
    def visit_app(self, e): return f"({e.arg1.accept(self)} {e.arg2.accept(self)})"
    def visit_if0(self, e): return f"(if {e.arg1.accept(self)} then {e.arg2.accept(self)} else {e.arg3.accept(self)})"
    def visit_let(self, e): return f"(let {e.arg1} = {e.arg2.accept(self)} in {e.arg3.accept(self)})"
    def visit_pair(self, e): return f"(pair {e.arg1.accept(self)} {e.arg2.accept(self)})"
    def visit_pfst(self, e): return f"(fst {e.arg1.accept(self)})"
    def visit_psnd(self, e): return f"(snd {e.arg1.accept(self)})"


def d0exp_pretty(expression: d0exp) -> str:
    return expression.accept(PrettyPrintVisitor())


class NameCollectorVisitor(D0ExpVisitor[set[str]]):
    """Collect every occurrence and binder name, not merely free names."""

    def visit_int(self, e): return set()
    def visit_btf(self, e): return set()
    def visit_var(self, e): return {e.arg1}
    def visit_op1(self, e): return e.arg1.accept(self)
    def visit_op2(self, e): return e.arg1.accept(self) | e.arg2.accept(self)
    def visit_lam(self, e): return {e.arg1} | e.arg2.accept(self)
    def visit_fix(self, e): return {e.arg1, e.arg2} | e.arg3.accept(self)
    def visit_app(self, e): return e.arg1.accept(self) | e.arg2.accept(self)
    def visit_if0(self, e): return e.arg1.accept(self) | e.arg2.accept(self) | e.arg3.accept(self)
    def visit_let(self, e): return {e.arg1} | e.arg2.accept(self) | e.arg3.accept(self)
    def visit_pair(self, e): return e.arg1.accept(self) | e.arg2.accept(self)
    def visit_pfst(self, e): return e.arg1.accept(self)
    def visit_psnd(self, e): return e.arg1.accept(self)


class AlphaRenameVisitor(D0ExpVisitor[d0exp]):
    """Rename occurrences bound by one already-entered binder.

    A nested binder with the old name shadows that binder, so its scoped region
    is deliberately left untouched.
    """
    def __init__(self, old: str, new: str): self.old, self.new = old, new
    def visit_int(self, e): return D0Eint(e.arg1)
    def visit_btf(self, e): return D0Ebtf(e.arg1)
    def visit_var(self, e): return D0Evar(self.new if e.arg1 == self.old else e.arg1)
    def visit_op1(self, e): return D0Eop1(e.name, e.arg1.accept(self))
    def visit_op2(self, e): return D0Eop2(e.name, e.arg1.accept(self), e.arg2.accept(self))
    def visit_lam(self, e):
        return D0Elam(e.arg1, e.arg2 if e.arg1 == self.old else e.arg2.accept(self))
    def visit_fix(self, e):
        return D0Efix(e.arg1, e.arg2, e.arg3 if self.old in {e.arg1, e.arg2} else e.arg3.accept(self))
    def visit_app(self, e): return D0Eapp(e.arg1.accept(self), e.arg2.accept(self))
    def visit_if0(self, e): return D0Eif0(e.arg1.accept(self), e.arg2.accept(self), e.arg3.accept(self))
    def visit_let(self, e):
        return D0Elet(e.arg1, e.arg2.accept(self), e.arg3 if e.arg1 == self.old else e.arg3.accept(self))
    def visit_pair(self, e): return D0Epair(e.arg1.accept(self), e.arg2.accept(self))
    def visit_pfst(self, e): return D0Epfst(e.arg1.accept(self))
    def visit_psnd(self, e): return D0Epsnd(e.arg1.accept(self))


class SubstitutionVisitor(D0ExpVisitor[d0exp]):
    """Perform one capture-avoiding substitution with immutable AST rebuilding."""
    def __init__(self, variable: str, replacement: d0exp, forbidden: set[str]):
        self.variable, self.replacement = variable, replacement
        self.replacement_fv = d0exp_fvset(replacement)
        self.forbidden, self.next_number = set(forbidden), 1

    def fresh(self, base: str) -> str:
        while f"{base}_{self.next_number}" in self.forbidden:
            self.next_number += 1
        result = f"{base}_{self.next_number}"
        self.forbidden.add(result)
        self.next_number += 1
        return result

    def should_rename(self, binder: str, body: d0exp) -> bool:
        return binder in self.replacement_fv and self.variable in d0exp_fvset(body)

    def visit_int(self, e): return D0Eint(e.arg1)
    def visit_btf(self, e): return D0Ebtf(e.arg1)
    def visit_var(self, e): return self.replacement if e.arg1 == self.variable else D0Evar(e.arg1)
    def visit_op1(self, e): return D0Eop1(e.name, e.arg1.accept(self))
    def visit_op2(self, e): return D0Eop2(e.name, e.arg1.accept(self), e.arg2.accept(self))
    def visit_app(self, e): return D0Eapp(e.arg1.accept(self), e.arg2.accept(self))
    def visit_if0(self, e): return D0Eif0(e.arg1.accept(self), e.arg2.accept(self), e.arg3.accept(self))
    def visit_pair(self, e): return D0Epair(e.arg1.accept(self), e.arg2.accept(self))
    def visit_pfst(self, e): return D0Epfst(e.arg1.accept(self))
    def visit_psnd(self, e): return D0Epsnd(e.arg1.accept(self))

    def visit_lam(self, e):
        if e.arg1 == self.variable:
            return D0Elam(e.arg1, e.arg2)
        name, body = e.arg1, e.arg2
        if self.should_rename(name, body):
            name = self.fresh(name)
            body = body.accept(AlphaRenameVisitor(e.arg1, name))
        return D0Elam(name, body.accept(self))

    def visit_let(self, e):
        init = e.arg2.accept(self)  # The binder does not scope over init.
        if e.arg1 == self.variable:
            return D0Elet(e.arg1, init, e.arg3)
        name, body = e.arg1, e.arg3
        if self.should_rename(name, body):
            name = self.fresh(name)
            body = body.accept(AlphaRenameVisitor(e.arg1, name))
        return D0Elet(name, init, body.accept(self))

    def visit_fix(self, e):
        # The parameter is the innermost fix binder; either matching target
        # prevents substitution throughout the body.
        if self.variable in {e.arg1, e.arg2}:
            return D0Efix(e.arg1, e.arg2, e.arg3)
        fun, param, body = e.arg1, e.arg2, e.arg3
        # With equal names, the parameter shadows the function throughout the
        # body, so renaming that outer function binder would be unnecessary.
        if fun != param and fun in self.replacement_fv and self.variable in d0exp_fvset(body):
            fresh_fun = self.fresh(fun)
            body = body.accept(AlphaRenameVisitor(fun, fresh_fun))
            fun = fresh_fun
        if param in self.replacement_fv and self.variable in d0exp_fvset(body):
            fresh_param = self.fresh(param)
            body = body.accept(AlphaRenameVisitor(param, fresh_param))
            param = fresh_param
        return D0Efix(fun, param, body.accept(self))


def d0exp_substitute(expression: d0exp, variable: str, replacement: d0exp) -> d0exp:
    """Return expression[variable := replacement], without evaluation or mutation."""
    names = expression.accept(NameCollectorVisitor()) | replacement.accept(NameCollectorVisitor()) | {variable}
    return expression.accept(SubstitutionVisitor(variable, replacement, names))
