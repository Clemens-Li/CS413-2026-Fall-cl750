# Assignment 05: Visitors for LAMBDA

Requires Python 3.12 or later. From `assigns/05`, install the only optional
test dependency with `python -m pip install pytest`. Run the independent suites
with:

```text
python -m unittest discover -s MySolution -p test_unittest.py
python -m pytest MySolution/test_pytest.py
```

`d0exp_pretty(D0Eapp(D0Evar("f"), D0Eint(4)))` returns `(f 4)`.  For
substitution, `d0exp_substitute(D0Elam("y", D0Evar("x")), "x",
D0Evar("y"))` prints as `(lam y_1. y)`.

Fresh names are deterministic. Each substitution first collects *all* variable
occurrences and binder names from the original expression and replacement, then
uses `base_1`, `base_2`, and so on, skipping every collected or previously
generated name. The counter is shared by all alpha-renames in one substitution;
therefore repeated calls give identical results. No known limitations apply to
the required AST forms.

## Reflection: Design Explanation

`PrettyPrintVisitor` has result type `str`; every expression's `accept` method
selects the appropriate method, which recursively prints its children without
calling the evaluator. `SubstitutionVisitor` instead has result type `d0exp`.
It carries the substitution target, replacement, the replacement's free-variable
set, and the fresh-name state. Each visit builds a new expression (or safely
reuses an untouched scoped subtree), so neither input AST is mutated. The name
collector and alpha-renamer are also visitors, keeping all expression traversal
within visitor dispatch rather than a central type test.

At a lambda or let body, substitution stops when that binder matches the target.
Otherwise, if a free target occurrence can be reached and the binder occurs
free in the replacement, the visitor alpha-renames the binder first. The
renamer stops at nested binders with the same old name, preserving lexical
shadowing. A `let` initializer is visited before these body rules because it is
outside the let scope. A `fix` has two binders; its parameter is inner, so the
visitor handles both conflicts in order and treats either target binder as
blocking body substitution. This also preserves the supplied evaluator's
same-name `fix` behavior.

Visitors make adding a new operation inexpensive: a new visitor supplies one
method per existing constructor and leaves the AST unchanged. Adding a new
expression constructor is the opposite tradeoff: it requires a new `accept`
method and a method in every existing visitor, including evaluation and the
new operations.


