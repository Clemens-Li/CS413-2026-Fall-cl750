"""Pure target AST, printer, free variables, capture-avoiding substitution, weak CBV reducer.

Printer, free-variable analysis, and fresh-name ideas adapt the author's Assignment 5
substitution work (supplied lambda1_vp.py is used only by the compiler, unmodified).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Lam:
    name: str
    body: "Term"


@dataclass(frozen=True)
class App:
    fn: "Term"
    arg: "Term"


Term = Var | Lam | App


@dataclass(frozen=True)
class EvalOutcome:
    value: Term
    status: str
    steps: int


def pretty_term(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    if isinstance(term, Lam):
        return f"(lam {term.name}. {pretty_term(term.body)})"
    if isinstance(term, App):
        return f"({pretty_term(term.fn)} {pretty_term(term.arg)})"
    raise TypeError(f"unsupported term: {type(term).__name__}")


def free_vars(term: Term) -> set[str]:
    if isinstance(term, Var):
        return {term.name}
    if isinstance(term, Lam):
        return free_vars(term.body) - {term.name}
    if isinstance(term, App):
        return free_vars(term.fn) | free_vars(term.arg)
    raise TypeError(f"unsupported term: {type(term).__name__}")


def all_names(term: Term) -> set[str]:
    """All names (free and bound) occurring in *term*.

    Alpha-renaming must avoid bound names too: avoiding only free names can
    make a renamed occurrence become captured by an inner binder.
    """
    if isinstance(term, Var):
        return {term.name}
    if isinstance(term, Lam):
        return {term.name} | all_names(term.body)
    if isinstance(term, App):
        return all_names(term.fn) | all_names(term.arg)
    raise TypeError(f"unsupported term: {type(term).__name__}")


def alpha_rename(term: Term, old: str, new: str) -> Term:
    def go(current: Term, renaming_scope: bool) -> Term:
        if isinstance(current, Var):
            return Var(new if renaming_scope and current.name == old else current.name)
        if isinstance(current, Lam):
            if current.name == old:
                if renaming_scope:
                    return Lam(current.name, go(current.body, False))
                return Lam(new, go(current.body, True))
            return Lam(current.name, go(current.body, renaming_scope))
        if isinstance(current, App):
            return App(go(current.fn, renaming_scope), go(current.arg, renaming_scope))
        raise TypeError(f"unsupported term: {type(current).__name__}")

    return go(term, False)


def choose_fresh(base: str, forbidden: Iterable[str]) -> str:
    taken = set(forbidden)
    idx = 0
    candidate = base
    while candidate in taken:
        idx += 1
        candidate = f"{base}_{idx}"
    return candidate


def substitute(term: Term, variable: str, replacement: Term) -> Term:
    if isinstance(term, Var):
        return replacement if term.name == variable else term

    if isinstance(term, Lam):
        if term.name == variable:
            return term
        if variable in free_vars(term.body):
            blocked = all_names(term.body) | all_names(replacement) | {variable}
            if term.name in free_vars(replacement):
                fresh = choose_fresh(term.name, blocked)
                # Rename the whole abstraction: alpha_rename renames the binder *and*
                # the bound occurrences in its body (stopping at inner rebinders).
                # Passing only term.body would leave bound occurrences untouched.
                renamed = alpha_rename(term, term.name, fresh)
                return Lam(renamed.name, substitute(renamed.body, variable, replacement))
        return Lam(term.name, substitute(term.body, variable, replacement))

    if isinstance(term, App):
        return App(substitute(term.fn, variable, replacement), substitute(term.arg, variable, replacement))

    raise TypeError(f"unsupported term: {type(term).__name__}")


def is_value(term: Term) -> bool:
    return isinstance(term, Lam)


def eval_target(term: Term, budget: int = 1000) -> EvalOutcome:
    """Weak, left-to-right call-by-value reduction for target terms."""
    if budget < 0:
        raise ValueError("budget must be nonnegative")
    names = free_vars(term)
    if names:
        raise ValueError(f"cannot execute open target term; free variables: {sorted(names)}")

    def loop(current: Term, remaining: int) -> tuple[Term, int, str]:
        if isinstance(current, Lam):
            return current, remaining, "complete"
        if isinstance(current, Var):
            raise ValueError(f"unbound target variable during execution: {current.name}")
        if not isinstance(current, App):
            raise TypeError(f"unsupported term: {type(current).__name__}")

        if remaining <= 0:
            return current, remaining, "exhausted"

        # Evaluate function first.
        if not isinstance(current.fn, Lam):
            fn_val, remaining_after_fn, fn_status = loop(current.fn, remaining)
            if fn_status == "exhausted":
                return App(fn_val, current.arg), remaining_after_fn, "exhausted"
            if not isinstance(fn_val, Lam):
                return App(fn_val, current.arg), remaining_after_fn, "complete"
            current = App(fn_val, current.arg)
        else:
            remaining_after_fn = remaining

        # Evaluate argument second.
        if not isinstance(current.arg, Lam):
            arg_val, remaining_after_arg, arg_status = loop(current.arg, remaining_after_fn)
            if arg_status == "exhausted":
                return App(current.fn, arg_val), remaining_after_arg, "exhausted"
            if not isinstance(arg_val, Lam):
                return App(current.fn, arg_val), remaining_after_arg, "complete"
            current = App(current.fn, arg_val)
        else:
            remaining_after_arg = remaining_after_fn

        # Apply beta only when the function is a lambda and the argument is a value.
        if not isinstance(current.fn, Lam):
            return current, remaining_after_arg, "complete"
        if remaining_after_arg <= 0:
            return current, remaining_after_arg, "exhausted"

        reduced = substitute(current.fn.body, current.fn.name, current.arg)
        remaining_after_arg -= 1
        result, remaining_after_reduction, status = loop(reduced, remaining_after_arg)
        if status == "exhausted":
            return result, remaining_after_reduction, "exhausted"
        return result, remaining_after_reduction, "complete"

    final_term, remaining, status = loop(term, budget)
    return EvalOutcome(final_term, status, budget - remaining)


__all__ = [
    "Var",
    "Lam",
    "App",
    "Term",
    "EvalOutcome",
    "pretty_term",
    "free_vars",
    "all_names",
    "alpha_rename",
    "choose_fresh",
    "substitute",
    "is_value",
    "eval_target",
]
