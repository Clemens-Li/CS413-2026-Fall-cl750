# Design and correctness argument

The source language is Assignment 5's visitor-based AST.  The target is deliberately separate and has exactly `Var(name)`, `Lam(name, body)`, and `App(fn, arg)`.  `target.py` supplies a conventional parenthesized printer, free-variable analysis, all-name analysis, alpha-renaming, and capture-avoiding substitution.  Fresh alpha names avoid *all* names in both terms, not merely free names: choosing an inner bound name could otherwise capture a newly renamed occurrence.

## Translation

Write `C[e]` for compilation.  Literals use the closed Church builders `NUM(n)`, `TRUE`, and `FALSE`; variables are preserved.  The remaining rules are:

```text
C[lam x. e]              = lam x. C[e]
C[e1 e2]                 = C[e1] C[e2]
C[let x = e1 in e2]     = (lam x. C[e2]) C[e1]
C[if c then t else f]   = C[c] (lam u. C[t]) (lam v. C[f]) I
C[not e]                 = NOT C[e]
C[e1 op e2]              = OP C[e1] C[e2]       (arithmetic/comparison)
C[e1 and e2]             = C[e1] (lam u. C[e2]) (lam v. FALSE) I
C[e1 or e2]              = C[e1] (lam u. TRUE) (lam v. C[e2]) I
C[pair(e1,e2)]           = PAIR C[e1] C[e2]
C[fst e], C[snd e]      = FST C[e], SND C[e]
C[fix f(x). e]          = Z (lam f. lam x. C[e])
```

`OP` is one of `ADD`, `SUB`, `MUL`, `LT`, `LE`, `GT`, `GE`, `EQ`, or `NEQ`.  Each is expanded into a closed target term, never left as a primitive.  Validation walks every source subtree before compilation, so a negative literal or unsupported operator is rejected even in a branch that would not be evaluated.  It never invokes evaluation.

The compiler collects every source identifier first.  Every binder it introduces (`u`, `v`, and source binder copies) is selected by a deterministic suffix policy (`base`, then `base_1`, and so on) against that collection and names already allocated.  Source binders are mapped through a lexical environment.  A let maps its name only in its body; a fix maps both names, except that coincident names map to the parameter, which correctly implements parameter shadowing.  This policy prevents generated capture and makes `FV(C[e]) = FV(e)`, including for open terms.

## Runtime and encodings

The shared entry point `evaluator.evaluate` dispatches on representation.  Target terms use the weak left-to-right call-by-value reducer: it evaluates function, then argument, contracts only `(lam x. body) value`, counts that beta-value contraction, and never descends beneath a lambda.  Closed target execution is required; an open term gets a useful error.  The source path uses the required left-to-right rules, truncated subtraction, pair strictness, and lazy conditional/boolean branches.  It is used only for terminating expected examples.  The evaluator never imports the compiler.

Booleans are `TRUE = lam t. lam f. t` and `FALSE = lam t. lam f. f`; numerals are `lam s. lam z. s^n z`; and a pair is `lam a. lam b. lam p. p a b`.  `FST` and `SND` select with those booleans.  Addition and multiplication use the normal iteration equations.  Subtraction iterates predecessor.  The predecessor is Kleene's continuation construction:

```text
PRED = lam n. lam s. lam z.
         n (lam g. lam h. h (g s)) (lam u. z) (lam u. u)
```

At zero the base continuation returns `z`; after each successor, the delayed continuation transfers exactly one `s`.  Consequently predecessor of zero is zero and subtraction is truncated.  `ISZERO` applies a constant-false step to a numeral; comparisons are defined from zero-test and subtraction.  `Z = lam g. (lam x. g (lam v. x x v)) (lam x. g (lam v. x x v))` is used instead of ordinary `Y`: its extra lambda delays self-application until an argument exists under CBV.

Delayed branch thunks are essential.  CBV would otherwise evaluate both branches before Church `TRUE` or `FALSE` could choose.  Supplying two lambda thunks and finally applying the selected thunk to closed identity `I` forces exactly one.  The same construction makes `and` and `or` short circuit.

## Observation and confidence

Results remain weak values, so decoding does not normalize under binders.  Natural observation applies a result to `STEP = lam tail. lam c. lam z. c tail` and `BASE = lam c. lam z. z`; the resulting finite spine is counted structurally.  Boolean observation uses two distinct closed markers.  Pair observation first evaluates the pair, separately projects both components, then uses each requested observer.  Execution and observation have independent reported budgets and counts; malformed shapes or observer exhaustion are reported rather than silently treated as answers.

The intended claim is: for a closed, well-typed source program in the assigned subset producing a natural, boolean, or finite pair, observing `C[e]` yields the same datum as source evaluation when both finite reduction budgets are sufficient.  Application and let follow beta-value substitution; the compiler preserves lexical binding through its environment.  Conditionals and boolean connectives preserve selected-branch behavior via thunks, while `Z` supplies the recursive closure behavior required by fix.  Tests exercise independent substitution, zero-step weak values, evaluation order, every operator, scope, open free variables, omitted divergent branches, pair strictness, closed-library structure, factorial, Fibonacci, and bounded loops.  This is evidence rather than a proof: a formal proof would require inducting over source evaluation and a logical relation for the Church representations, and bounded tests cannot establish semantic equivalence for all programs.

## Module interfaces

Each module exposes a small surface so that the compiler, the runtime, and the decoders can be reviewed independently.

- `target.py`: `Var`, `Lam`, `App`; `pretty_term`, `free_vars`, `all_names`, `substitute`, and `eval_target(term, budget) -> EvalOutcome(value, status, steps)`. It knows nothing about the source language.
- `church_encodings.py` (implemented in `encodings.py`): closed target terms and the builder `NUM(n)`. It depends only on `target.py`. The public name differs from the file name because `encodings` collides with Python's standard-library package of the same name.
- `compiler.py`: `compile_expr(source) -> Term` and `CompileVisitor`, a subclass of Assignment 5's `D0ExpVisitor`. It imports the encodings and the target AST but never the evaluator.
- `evaluator.py`: `evaluate(expr, budget=None)`, the single entry point. A target term is dispatched to `eval_target`; a source AST is interpreted with the source rules. It never imports the compiler.
- `observers.py`: `observe_nat`, `observe_bool`, and `observe_pair`, each returning `(value, steps, status)`.
- `demo.py` and `test_selfcheck.py` sit on top of all of these and are the only places where compilation, execution, and observation are chained.

## Status and error representation

Three outcomes are deliberately kept apart. A *complete* outcome carries a lambda value and the number of beta-value steps used. An *exhausted* outcome means another beta-value step was required with no budget left; it carries the partially reduced term and the steps spent, and it is never reported as proof of nontermination. A *rejection* is an exception: `ValueError` for an open target term, a negative literal, an unsupported operator, or an observation output with the wrong shape. Observers return the status string `"complete"` or `"exhausted"` as their third component, so an exhausted observation can never be mistaken for a decoded answer. Execution and observation budgets are separate arguments, and the demonstration prints both counts on distinct lines.

## Design tradeoffs

**Simplicity over speed in the reducer.** The reducer substitutes eagerly and recurses in Python, which makes the beta-value step count easy to audit against the specification. The price is cost: each contraction re-walks the body to compute free names, and long chains of sequential steps are bounded by Python's recursion depth. A closure-based machine or an explicit stack would be faster, but it would obscure the correspondence between the code and the stated reduction rule. The demonstrations therefore use modest inputs (factorial 4, Fibonacci 5), and deliberate loops use a small budget.

**Reserving every source name.** The compiler reserves all source identifiers, free and bound, before choosing any generated binder. This is slightly conservative because it renames some source binders to `base_1` even when no clash exists. In exchange the policy is uniform, deterministic, and easy to argue correct: a generated name can never equal a source name, so it can never capture one.

**Closed library terms.** Every library combinator is closed and uses its own suffixed binder names such as `s0` and `z0`. Because substitution during execution only ever inserts closed values, the library cannot capture source variables, and the library never forces the compiler to avoid names like `s` or `z`.

**Syntactic observers.** Decoders apply the result to pure observation contexts evaluated by the same engine, and only then inspect the final shape. They do not reduce beneath lambdas, which fits the weak semantics, but they also accept some ill-typed shapes leniently because the assignment does not require recognizing every invalid untyped encoding. The caller must name the expected kind because `NUM(0)` and `FALSE` are the same term.

**Strict arguments are intentional.** Under call-by-value, `(lam x. 0) LOOP` diverges even though `x` is unused, and a diverging let initializer or pair component does the same. The compiler preserves this by translating let and pair construction with ordinary application, and only conditionals and `and`/`or` receive thunks.

## Attribution

The printer format, free-variable analysis, and fresh-name approach adapt ideas from the Assignment 5 substitution work. The visitor interface and source AST are the supplied `lambda1_vp.py`, unchanged. The Church numeral, boolean, and pair representations follow the assignment statement. The predecessor is Kleene's classical construction, and `Z` is the standard call-by-value fixed-point combinator given in the assignment. AI assistance is recorded in `AI-TRANSCRIPT.md`.

## Verification snapshot

The documented self-check command was run on October 26, 2026 and completed all 19 `unittest` cases successfully. The demonstration command then completed all 14 required examples. In particular, compiled factorial applied to 4 completed execution in 493 beta-value steps and decoded to 24; compiled Fibonacci applied to 5 completed execution in 1,013 steps and decoded to 5. Observation took 1,245 and 405 steps respectively under the separate 200,000-step observation budget. The strict-function-argument and direct-loop demonstrations each exhausted the deliberately smaller 500-step execution budget. These concrete counts are implementation observations, not requirements of the language semantics.
