"""The shared call-by-value evaluator required by Assignment 6.

``evaluate`` dispatches only on AST representation: target terms go through
the pure reducer, while source nodes use the source-language rules.  It never
imports the compiler, so compilation is not accidentally used as evaluation.
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass

from target import EvalOutcome, Term, eval_target


@dataclass(frozen=True)
class SourceClosure:
    parameter: str
    body: object
    environment: dict[str, object]


@dataclass(frozen=True)
class SourceFixClosure:
    function: str
    parameter: str
    body: object
    environment: dict[str, object]


def _source_module():
    """Find the supplied Assignment 5 AST without modifying it."""
    try:
        import lambda1_vp
        return lambda1_vp
    except ModuleNotFoundError:
        parent = pathlib.Path(__file__).resolve().parents[2] / "05"
        sys.path.insert(0, str(parent))
        import lambda1_vp
        return lambda1_vp


def evaluate(expr: object, budget: int | None = None, environment: dict[str, object] | None = None):
    """Evaluate either a closed target term or a source AST.

    Target evaluation returns :class:`target.EvalOutcome` and requires a
    nonnegative budget.  Source evaluation is intentionally unbounded because
    it is used only for the terminating expected examples in the brief.
    """
    if isinstance(expr, (Term.__args__)):
        return eval_target(expr, 1000 if budget is None else budget)
    ast = _source_module()
    env = {} if environment is None else dict(environment)

    def go(node, rho):
        if isinstance(node, ast.D0Eint):
            if node.arg1 < 0:
                raise ValueError(f"negative literal outside source language: {node.arg1}")
            return node.arg1
        if isinstance(node, ast.D0Ebtf): return node.arg1
        if isinstance(node, ast.D0Evar):
            if node.arg1 not in rho: raise ValueError(f"unbound source variable: {node.arg1}")
            return rho[node.arg1]
        if isinstance(node, ast.D0Elam): return SourceClosure(node.arg1, node.arg2, dict(rho))
        if isinstance(node, ast.D0Efix): return SourceFixClosure(node.arg1, node.arg2, node.arg3, dict(rho))
        if isinstance(node, ast.D0Eapp):
            fn, arg = go(node.arg1, rho), go(node.arg2, rho)
            if isinstance(fn, SourceClosure):
                next_rho = dict(fn.environment); next_rho[fn.parameter] = arg
                return go(fn.body, next_rho)
            if isinstance(fn, SourceFixClosure):
                next_rho = dict(fn.environment); next_rho[fn.function] = fn; next_rho[fn.parameter] = arg
                return go(fn.body, next_rho)
            raise TypeError("source application requires a function")
        if isinstance(node, ast.D0Eif0):
            return go(node.arg2 if go(node.arg1, rho) else node.arg3, rho)
        if isinstance(node, ast.D0Elet):
            value = go(node.arg2, rho); next_rho = dict(rho); next_rho[node.arg1] = value
            return go(node.arg3, next_rho)
        if isinstance(node, ast.D0Epair): return (go(node.arg1, rho), go(node.arg2, rho))
        if isinstance(node, ast.D0Epfst): return go(node.arg1, rho)[0]
        if isinstance(node, ast.D0Epsnd): return go(node.arg1, rho)[1]
        if isinstance(node, ast.D0Eop1):
            if node.name != "not": raise ValueError(f"unsupported unary operator: {node.name}")
            return not go(node.arg1, rho)
        if isinstance(node, ast.D0Eop2):
            left = go(node.arg1, rho)
            if node.name == "and": return left and go(node.arg2, rho)
            if node.name == "or": return left or go(node.arg2, rho)
            right = go(node.arg2, rho)
            match node.name:
                case "+": return left + right
                case "-": return max(left - right, 0)
                case "*": return left * right
                case "<": return left < right
                case "<=": return left <= right
                case ">": return left > right
                case ">=": return left >= right
                case "==": return left == right
                case "!=": return left != right
                case _: raise ValueError(f"unsupported binary operator: {node.name}")
        raise TypeError(f"unsupported source expression: {type(node).__name__}")
    return go(expr, env)


__all__ = ["evaluate", "SourceClosure", "SourceFixClosure"]
