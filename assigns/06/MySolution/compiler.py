from __future__ import annotations

from lambda1_vp import (
    D0Eapp,
    D0Ebtf,
    D0Efix,
    D0Eif0,
    D0Eint,
    D0Elet,
    D0Eop1,
    D0Eop2,
    D0Epair,
    D0Epfst,
    D0Epsnd,
    D0Evar,
    D0Elam,
    D0ExpVisitor,
    d0exp,
)
from target import App, Lam, Term, Var
from church_encodings import ADD, EQ, FALSE, FST, GE, GT, I, LE, LT, MUL, NEQ, NOT, PAIR, SND, SUB, TRUE, Z, NUM

_SUPPORTED_BINARY = {"+", "-", "*", "<", "<=", ">", ">=", "==", "!=", "and", "or"}
_ARITHMETIC = {
    "+": ADD,
    "-": SUB,
    "*": MUL,
    "<": LT,
    "<=": LE,
    ">": GT,
    ">=": GE,
    "==": EQ,
    "!=": NEQ,
}


def _collect_names(expr: d0exp) -> set[str]:
    if isinstance(expr, D0Eint):
        return set()
    if isinstance(expr, D0Ebtf):
        return set()
    if isinstance(expr, D0Evar):
        return {expr.arg1}
    if isinstance(expr, D0Elam):
        return _collect_names(expr.arg2) | {expr.arg1}
    if isinstance(expr, D0Efix):
        return _collect_names(expr.arg3) | {expr.arg1, expr.arg2}
    if isinstance(expr, D0Eapp):
        return _collect_names(expr.arg1) | _collect_names(expr.arg2)
    if isinstance(expr, D0Eif0):
        return _collect_names(expr.arg1) | _collect_names(expr.arg2) | _collect_names(expr.arg3)
    if isinstance(expr, D0Elet):
        return _collect_names(expr.arg2) | _collect_names(expr.arg3) | {expr.arg1}
    if isinstance(expr, D0Epair):
        return _collect_names(expr.arg1) | _collect_names(expr.arg2)
    if isinstance(expr, D0Epfst):
        return _collect_names(expr.arg1)
    if isinstance(expr, D0Epsnd):
        return _collect_names(expr.arg1)
    if isinstance(expr, D0Eop1):
        return _collect_names(expr.arg1)
    if isinstance(expr, D0Eop2):
        return _collect_names(expr.arg1) | _collect_names(expr.arg2)
    raise TypeError(f"unsupported expression type: {type(expr).__name__}")


def _validate_source(expr: d0exp) -> None:
    if isinstance(expr, D0Eint):
        if expr.arg1 < 0:
            raise ValueError(f"unsupported negative literal: {expr.arg1}")
        return
    if isinstance(expr, D0Ebtf):
        return
    if isinstance(expr, D0Evar):
        return
    if isinstance(expr, D0Elam):
        _validate_source(expr.arg2)
        return
    if isinstance(expr, D0Efix):
        _validate_source(expr.arg3)
        return
    if isinstance(expr, D0Eapp):
        _validate_source(expr.arg1)
        _validate_source(expr.arg2)
        return
    if isinstance(expr, D0Eif0):
        _validate_source(expr.arg1)
        _validate_source(expr.arg2)
        _validate_source(expr.arg3)
        return
    if isinstance(expr, D0Elet):
        _validate_source(expr.arg2)
        _validate_source(expr.arg3)
        return
    if isinstance(expr, D0Epair):
        _validate_source(expr.arg1)
        _validate_source(expr.arg2)
        return
    if isinstance(expr, D0Epfst):
        _validate_source(expr.arg1)
        return
    if isinstance(expr, D0Epsnd):
        _validate_source(expr.arg1)
        return
    if isinstance(expr, D0Eop1):
        if expr.name != "not":
            raise ValueError(f"unsupported unary operator: {expr.name}")
        _validate_source(expr.arg1)
        return
    if isinstance(expr, D0Eop2):
        if expr.name not in _SUPPORTED_BINARY:
            raise ValueError(f"unsupported binary operator: {expr.name}")
        _validate_source(expr.arg1)
        _validate_source(expr.arg2)
        return
    raise TypeError(f"unsupported expression type: {type(expr).__name__}")


def _fresh(base: str, reserved: set[str]) -> str:
    index = 0
    candidate = base
    while candidate in reserved:
        index += 1
        candidate = f"{base}_{index}"
    reserved.add(candidate)
    return candidate


class CompileVisitor(D0ExpVisitor[Term]):
    """Compositional translation of each source constructor to a pure term."""

    def __init__(self, env: dict[str, str], reserved: set[str]) -> None:
        self.env = env
        self.reserved = reserved

    def _name(self, base: str) -> str:
        name = _fresh(base, self.reserved | set(self.env.values()))
        self.reserved.add(name)
        return name

    def _compile(self, expr: d0exp, env: dict[str, str] | None = None) -> Term:
        child = CompileVisitor(self.env if env is None else env, self.reserved)
        return expr.accept(child)

    def visit_int(self, dexp: D0Eint) -> Term:
        return NUM(dexp.arg1)

    def visit_btf(self, dexp: D0Ebtf) -> Term:
        return TRUE if dexp.arg1 else FALSE

    def visit_var(self, dexp: D0Evar) -> Term:
        return Var(self.env.get(dexp.arg1, dexp.arg1))

    def visit_lam(self, dexp: D0Elam) -> Term:
        local_name = self._name(dexp.arg1)
        local_env = dict(self.env)
        local_env[dexp.arg1] = local_name
        return Lam(local_name, self._compile(dexp.arg2, local_env))

    def visit_app(self, dexp: D0Eapp) -> Term:
        return App(self._compile(dexp.arg1), self._compile(dexp.arg2))

    def visit_let(self, dexp: D0Elet) -> Term:
        local_name = self._name(dexp.arg1)
        init_term = self._compile(dexp.arg2)
        local_env = dict(self.env)
        local_env[dexp.arg1] = local_name
        return App(Lam(local_name, self._compile(dexp.arg3, local_env)), init_term)

    def visit_pair(self, dexp: D0Epair) -> Term:
        return App(App(PAIR, self._compile(dexp.arg1)), self._compile(dexp.arg2))

    def visit_pfst(self, dexp: D0Epfst) -> Term:
        return App(FST, self._compile(dexp.arg1))

    def visit_psnd(self, dexp: D0Epsnd) -> Term:
        return App(SND, self._compile(dexp.arg1))

    def visit_if0(self, dexp: D0Eif0) -> Term:
        cond = self._compile(dexp.arg1)
        u = self._name("u")
        v = self._name("v")
        then_term = self._compile(dexp.arg2)
        else_term = self._compile(dexp.arg3)
        return App(App(App(cond, Lam(u, then_term)), Lam(v, else_term)), I)

    def visit_op1(self, dexp: D0Eop1) -> Term:
        if dexp.name != "not":
            raise ValueError(f"unsupported unary operator: {dexp.name}")
        return App(NOT, self._compile(dexp.arg1))

    def visit_op2(self, dexp: D0Eop2) -> Term:
        left = self._compile(dexp.arg1)
        right = self._compile(dexp.arg2)
        if dexp.name == "and":
            u = self._name("u")
            v = self._name("v")
            return App(App(App(left, Lam(u, right)), Lam(v, FALSE)), I)
        if dexp.name == "or":
            u = self._name("u")
            v = self._name("v")
            return App(App(App(left, Lam(u, TRUE)), Lam(v, right)), I)
        if dexp.name in _ARITHMETIC:
            return App(App(_ARITHMETIC[dexp.name], left), right)
        raise ValueError(f"unsupported binary operator: {dexp.name}")

    def visit_fix(self, dexp: D0Efix) -> Term:
        f_name = self._name(dexp.arg1)
        x_name = self._name(dexp.arg2)
        body_env = dict(self.env)
        if dexp.arg1 == dexp.arg2:
            body_env[dexp.arg1] = x_name
        else:
            body_env[dexp.arg1] = f_name
            body_env[dexp.arg2] = x_name
        body = self._compile(dexp.arg3, body_env)
        return App(Z, Lam(f_name, Lam(x_name, body)))


def compile_expr(expr: d0exp) -> Term:
    _validate_source(expr)
    reserved = _collect_names(expr)
    return expr.accept(CompileVisitor({}, reserved))


__all__ = ["compile_expr", "CompileVisitor"]
