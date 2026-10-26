# Assignment 6: Extended LAMBDA to pure lambda calculus

Requires Python 3.12+ and only the standard library.  From `assigns/06/` run:

```text
python MySolution/test_selfcheck.py
python MySolution/demo.py
```

The first command runs the automated regression suite.  The second prints every required source example, its generated pure target term, execution and observation budgets/counts, decoded result, and expected result.  Normal terminating demonstrations use a 200,000-step execution/observation budget; deliberate loops use a 500-step execution budget and report exhaustion.

Modules: `target.py` provides the separate `Var | Lam | App` AST, printer, free-name analysis, capture-avoiding substitution, and weak CBV reducer. `church_encodings.py` exposes the pure Church library (its implementation is retained in `encodings.py`; the public name avoids collision with Python's standard `encodings` package). `compiler.py` translates through Assignment 5's `D0ExpVisitor`. `evaluator.py` is the shared source/target evaluator and deliberately does not import the compiler. `observers.py` decodes bounded natural/boolean/pair observation contexts, including nested pairs. `demo.py` is the executable collection. `test_selfcheck.py` is the `unittest` regression suite for the Assign06 testing obligations.

Target execution is intentionally restricted to closed terms and rejects an open term with its free-name list. Compilation itself accepts open source expressions and preserves their free-variable sets. Step exhaustion only says another beta-value step was required; it is not a proof of nontermination. The reducer is deliberately simple and recursive, so demonstrations use modest bounds for divergent programs.

Code uses no external libraries.  The supplied Assignment 5 source AST is read but never modified.  The Church predecessor follows the standard Kleene delayed-continuation construction; its zero case selects the base continuation, while each successor transfers one application of the step function through the continuation chain.

`AI-TRANSCRIPT.md` records the assistance used to build and review this submission.

## Presentation and recording materials

`Assignment06_Presentation.html` is the 14-slide browser presentation for this project. Open it in a modern browser and use the arrow keys, Space, Page Up, or Page Down to navigate. `RECORDING_OUTLINE.txt` is a 15-minute speaker outline matched to those slides; it includes the planned live-demo checkpoints and timing.

## Verified status

On October 26, 2026, `python MySolution/test_selfcheck.py` completed successfully: 13 tests passed. `python MySolution/demo.py` completed all 14 required demonstrations. The terminating recursive examples decoded factorial 4 as 24 and Fibonacci 5 as 5; the two deliberate looping examples exhausted their 500-step execution budget as intended.
