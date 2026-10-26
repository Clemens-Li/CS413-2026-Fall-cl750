from __future__ import annotations

from target import App, Lam, Term, Var, eval_target, free_vars


def _strip_identity(term: Term) -> Term:
    if isinstance(term, App):
        fn = _strip_identity(term.fn)
        arg = _strip_identity(term.arg)
        if isinstance(fn, Lam) and isinstance(fn.body, Var) and fn.body.name == fn.name:
            return arg
        return App(fn, arg)
    if isinstance(term, Lam):
        return Lam(term.name, _strip_identity(term.body))
    return term


def _unwrap_dead_lambdas(term: Term) -> Term:
    while isinstance(term, Lam) and term.name not in free_vars(term.body):
        term = term.body
    return term


def _decode_bool(value: Term) -> bool:
    value = _unwrap_dead_lambdas(value)
    if isinstance(value, Lam):
        if isinstance(value.body, Lam):
            chosen = value.body.body
            if isinstance(chosen, Var) and chosen.name == value.name:
                return True
            if isinstance(chosen, Var) and chosen.name == value.body.name:
                return False
        elif isinstance(value.body, Var) and value.body.name == value.name:
            return False
    raise ValueError(f"malformed Church boolean: {value!r}")


def _decode_nat(value: Term) -> int:
    """Decode a Church numeral observed under STEP/BASE.

    The observation context evaluates n to a finite spine of the form
      λc. λz. z
    or
      λc. λz. c tail
    where tail is the recursively encoded predecessor.
    """
    if not isinstance(value, Lam) or not isinstance(value.body, Lam):
        raise ValueError(f"malformed Church numeral: {value!r}")

    c_name = value.name
    z_name = value.body.name
    body = value.body.body

    if isinstance(body, Var) and body.name == z_name:
        return 0
    if not isinstance(body, App):
        raise ValueError(f"malformed Church numeral: {value!r}")
    if not isinstance(body.fn, Var) or body.fn.name != c_name:
        raise ValueError(f"malformed Church numeral: {value!r}")

    return 1 + _decode_nat(body.arg)


def observe_bool(term: Term, budget: int = 1000):
    """Decode a Church boolean by applying it to two marker lambdas."""
    true_marker = Lam("a", Lam("b", Var("a")))
    false_marker = Lam("a", Lam("b", Var("b")))
    outcome = eval_target(App(App(term, true_marker), false_marker), budget)
    if outcome.status == "exhausted":
        return None, outcome.steps, "exhausted"
    value = _strip_identity(outcome.value)
    return _decode_bool(value), outcome.steps, "complete"


def observe_nat(term: Term, budget: int = 1000):
    """Decode a Church numeral using the standard STEP/BASE observation context."""
    step = Lam("tail", Lam("c", Lam("z", App(Var("c"), Var("tail")))))
    base = Lam("c", Lam("z", Var("z")))
    outcome = eval_target(App(App(term, step), base), budget)
    if outcome.status == "exhausted":
        return None, outcome.steps, "exhausted"
    value = _strip_identity(outcome.value)
    return _decode_nat(value), outcome.steps, "complete"


def _observe_by_kind(term: Term, kind, budget: int):
    if kind == "nat":
        return observe_nat(term, budget)
    if kind == "bool":
        return observe_bool(term, budget)
    if isinstance(kind, tuple) and len(kind) == 2:
        return observe_pair(term, kind[0], kind[1], budget)
    raise ValueError(f"unsupported observation kind: {kind!r}")


def observe_pair(term: Term, left_kind="nat", right_kind="nat", budget: int = 1000):
    """Evaluate a Church pair and decode both components using the supplied kinds.

    A component kind is ``"nat"``, ``"bool"``, or a nested ``(left, right)`` pair
    description, so ``pair (pair 2 true) 3`` can be observed as
    ``(("nat", "bool"), "nat")``.
    """
    outcome = eval_target(term, budget)
    if outcome.status == "exhausted":
        return None, outcome.steps, "exhausted"
    from church_encodings import FST, SND

    child_budget = max(1, budget // 2)
    left_outcome = eval_target(App(FST, outcome.value), child_budget)
    right_outcome = eval_target(App(SND, outcome.value), child_budget)
    if left_outcome.status == "exhausted" or right_outcome.status == "exhausted":
        return None, outcome.steps + left_outcome.steps + right_outcome.steps, "exhausted"

    left_value, left_obs, left_status = _observe_by_kind(left_outcome.value, left_kind, child_budget)
    if left_status == "exhausted":
        return None, outcome.steps + left_outcome.steps + left_obs, "exhausted"
    right_value, right_obs, right_status = _observe_by_kind(right_outcome.value, right_kind, child_budget)
    if right_status == "exhausted":
        return None, outcome.steps + right_outcome.steps + right_obs, "exhausted"

    steps = outcome.steps + left_outcome.steps + right_outcome.steps + left_obs + right_obs
    return (left_value, right_value), steps, "complete"


__all__ = ["observe_bool", "observe_nat", "observe_pair"]
