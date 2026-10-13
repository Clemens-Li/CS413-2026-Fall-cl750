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

I used the same expression tree for both operations, but their visitors return
different kinds of results. `PrettyPrintVisitor` returns a `str`. Each AST
node's `accept` method dispatches to the matching visitor method, and that
method formats the node while asking the visitor to print any child
expressions. This keeps printing separate from evaluation: even an expression
that would fail at runtime, such as division by zero, can still be displayed.

`SubstitutionVisitor` returns a `d0exp`, because its job is to build the
substituted expression rather than a string. It carries the target variable,
the replacement expression, the replacement's free variables, and the set of
names that fresh-name generation must avoid. The name set includes all
occurrences and binders in both input expressions, as well as the target.
A shared counter makes fresh names deterministic across multiple renames in
one call. The visitor reconstructs transformed nodes and may reuse a scoped
subtree when substitution is blocked; it does not change either input tree or
evaluate the result.

The important part of substitution is respecting where each name is bound.
For a lambda, a binder matching the target blocks substitution in its body.
Otherwise, if the body contains a free target and the replacement contains
the binder name free, the binder must be renamed before substitution. The
alpha-renaming visitor changes only occurrences belonging to that binder: it
stops at a nested binder with the same name, since that inner binder shadows
the outer one. A `let` name scopes over its body, not its initializer, so the
initializer is always processed separately. A `fix` has two nested binders;
the function name is outer and the parameter is inner. Handling them in that
order preserves shadowing, including the case where both names are identical.
The collector and renamer are visitors too, so expression traversal continues
to use `accept` rather than a central series of type checks.

This design makes adding an operation relatively localized: a new visitor
implements one method for each existing expression form, while the AST stays
the same. Adding a new expression form has a wider cost. Its class needs an
`accept` method, and every visitor must learn how to handle it—including
printing, substitution, free-variable analysis, and evaluation. In short,
visitors make new operations straightforward, but new node types require
updating the operations that already exist.

