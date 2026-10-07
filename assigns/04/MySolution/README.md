# LAMBDA Workbench

A local MVC website for the supplied LAMBDA interpreter (`lambda1.py`). Python 3.12+; tested with Python 3.12+ and 3.14 on Windows/Linux. No third-party dependencies, installation, or build step.

```sh
cd assigns/04/MySolution
python app.py --port 8040
```

Open http://127.0.0.1:8040. The default port, if omitted, is 8000. Stop with Ctrl+C. The server binds only to loopback. Use one browser tab: server state is shared by tabs, is kept in memory, and resets on restart. Uploaded files are never modified. Keep source files on disk if you need them after a restart.

```sh
python -m unittest discover -s tests -v
node --check static/app.js
node tests/browser-runtime.cjs
# With the server running on port 8040:
python tests/http_smoke.py
```

## Try it

1. Load source → Factorial (canned), then Interpret: `D0Vint(arg1=120)`.
2. Load Fibonacci (canned), then Interpret: `D0Vint(arg1=55)`. Edit its final input, Apply changes, and run again.
3. Choose Manual input, enter `D0Evar("x")`, Apply changes, and Lint. The output lists `x` as undeclared. Replace it with `D0Elam("x", D0Evar("x"))`, apply, and lint again: no free variables.
4. Load Runtime error. Lint succeeds, but Interpret reports division by zero. Closed expressions are not necessarily valid at runtime.
5. Type-check and Compile explicitly return not-implemented results. Execute remains disabled because there is no generated code.

Typing enables Apply changes and Discard changes. Until edits are resolved, tools and source replacement are disabled. Ctrl/Cmd+Enter applies edits. Results identify their operation, revision, and outcome. Every accepted replacement clears old results.

## Input and limits

Input is one Python constructor expression, with positional arguments, literal strings/integers/Booleans, nested constructors, comments, and multiline formatting. It is not a Python script: imports, attributes, arbitrary calls, comprehensions, and keyword arguments are rejected. See the constructor reference in the page and `examples/`. `D0E000` is an abstract error form and is not accepted as source. Unary integer negation is supported. Operators follow `lambda1.py`; integer division uses `/` as the operator string.

Use the canonical constructor prefix `D0E` (with zero), for example `D0Eop2("+", D0Eint(20), D0Eint(22))`, which evaluates to `D0Vint(arg1=42)`. For compatibility, the workbench also accepts the visually similar `DOE` prefix, so `DOEop2("+", DOEint(20), DOEint(22))` has the same result. Both the server interpreter and offline browser fallback normalize it to the canonical LAMBDA nodes.

Source is limited to 65,536 UTF-8 bytes. Each backend operation runs in a subprocess with a three-second wall-clock timeout (and, on Unix, a three-second CPU limit and a 256 MiB address-space limit). Python recursion limits may terminate recursive programs earlier. Very large values may exceed Python's integer-to-string limit. These resource bounds are for a local educational tool, not a public service. Actual type-checking, compilation, generated-code execution, and multi-user support are not implemented.

## Offline browser fallback

Opening `static/index.html` directly as a local file (or through a static HTTP server without `app.py`) uses a hand-written JavaScript port in `static/runtime.js`. That path keeps the same UI and adapter contract offline; it is not automatically generated compiler output. Integers use BigInt, including Python-style floor division. Changes to the Python implementation or examples must also be reflected in the port. Run `node tests/browser-runtime.cjs` for parity checks.

## Reflection

MVC helped treat applied source as application state, not whatever text happens to sit in the editor. The model owns revisions, result history, busy state, and artifact invalidation, so those rules can be unit-tested without a server. The controller is the only module that calls the language adapter and is responsible for returning the model to idle after a failure. The view can then show drafts, controls, and textual results without knowing how `d0exp_fvset` or `d0exp_evaluate` are invoked.

The hard boundary was the browser draft versus applied source. Sending every keystroke to the server would add chatter and another synchronization problem. Committing complete expressions with Apply and Discard is simpler, but it assumes one tab. A later multi-tab design should send an expected revision and reject stale writes.

The restricted constructor reader was another useful cut. It validates input before any language tool runs and never executes uploaded Python. Lint and interpret share that reader, but lint still must not evaluate. A bounded worker keeps a nonterminating program from freezing the HTTP server.

A future compiler can replace one adapter operation, store a revision-associated artifact on the model, and let Execute consume that artifact without silently recompiling. The view would keep rendering ordinary `{operation, revision, outcome, text}` records. That change needs artifact validation and new tests, not a fake “compile” that just interprets.
