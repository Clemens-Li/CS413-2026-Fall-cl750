# Verification — October 6, 2026

Environment: Windows 10, Python 3.14.2, Node.js v22.22.0, Chrome (headless CDP).

```sh
python -m unittest discover -s tests -v   # 8 tests OK
node --check static/app.js
node tests/browser-runtime.cjs            # JS runtime + Python parity OK
python app.py --port 8040                 # in another terminal
python tests/http_smoke.py                # 20/20 live HTTP checks OK
```

## Automated coverage (assignment list)

| # | Requirement | Test | Result |
| --- | --- | --- | --- |
| 1 | Free variables for every constructor, duplicates, nested bindings, `fix`, let-initializer scope; result is `frozenset` | `LanguageTests.test_scope_and_all_constructors` | pass |
| 2 | Lint success on closed programs; sorted names on open programs; lint does not evaluate division by zero | `LanguageTests.test_lint_does_not_evaluate_and_errors` | pass |
| 3 | Interpret arithmetic=42, factorial=120, Fibonacci=55 plus base cases; malformed input and runtime failures | `LanguageTests.test_real_examples_and_base_cases`, `test_lint_does_not_evaluate_and_errors` | pass |
| 4 | Manual apply, replacement, rejection of empty/oversize without losing applied source | `StateTests.test_revision_and_rejection` (no browser/server) | pass |
| 5 | Placeholders are `not_implemented`; Execute unavailable | `StateTests.test_placeholders_and_execute` | pass |
| 6 | Busy rejection, injected backend failure, idle restore, successful retry; timeout path | `StateTests.test_dispatch_failure_busy_and_retry` (fake backend, no view change); `LanguageTests.test_timeout` | pass |

`tests/http_smoke.py` repeats load/lint/interpret, placeholders, Execute rejection, empty/oversize preservation, and HTML-like result text against the live server.

## Browser smoke test

Command: start `python app.py --port 8040`, then Chrome with `--remote-debugging-port=9224`, then `node --experimental-websocket tests/browser-smoke.mjs`.

| Step | Expected | Observed |
| --- | --- | --- |
| Load Factorial, Interpret | Result text includes `120` | Pass |
| Load Fibonacci, Interpret | Result text includes `55` | Pass |
| Load Manual input | Editor is blank | Pass |
| Type `D0Evar("<img src=x onerror=alert(1)>")` | Load menu and Lint disabled while dirty | Pass |
| Apply, then Lint | Output shows `<img` as text; no `img` element in the results pane | Pass |
| Apply whitespace | Notice shown; editor keeps `   `; applied source unchanged until Discard | Pass |
| Discard, apply `D0Eop2("/", D0Eint(1), D0Eint(0))`, Lint then Interpret | Lint `success`; Interpret `runtime_error` | Pass |
| Type-check, Compile | Last outcome `not_implemented`; Execute remains disabled | Pass |
| Load Arithmetic, Interpret | Recovery; text includes `42` | Pass |
| Upload invalid UTF-8 | Notice includes `UTF-8`; previous applied source kept | Pass |
| Upload `D0Eint(7)`, Interpret | Name `seven.lambda`; result includes `7` | Pass |
| Reload Factorial, Lint and Interpret | Session still usable after errors | Pass |
| Viewport 390×844 | No horizontal overflow | `Mobile overflow: false` |

Screenshot written to the OS temp directory as `lambda-workbench.png` and inspected.

## F1–F10 traceability

| ID | Check and observed result |
| --- | --- |
| F1 | Browser loaded Factorial/Fibonacci, blank manual editor, and a UTF-8 upload; HTTP smoke confirmed canned examples. |
| F2 | Dirty editor disabled tools and the load menu; Apply committed; Discard restored applied source. |
| F3 | Browser rejected whitespace and invalid UTF-8, keeping applied source and rejected editor text; model/HTTP tests rejected oversize input. |
| F4 | Buttons appear Lint, Interpret, Type-check, Compile, Execute; tools disabled without applied source or while dirty; Execute stays disabled. |
| F5 | Scope unit tests passed; browser/HTTP showed undeclared names and successful closed lint. |
| F6 | Factorial=120, Fibonacci=55, arithmetic=42; malformed input vs runtime errors distinguished. |
| F7 | Type-check/Compile returned not-implemented; Execute stayed disabled/rejected with an artifact explanation. |
| F8 | Model and HTTP tests: revision increments, cleared history/artifacts, preserved state on rejection. |
| F9 | HTML-like names rendered with `textContent`; results show operation, revision, and outcome. |
| F10 | Fake backend saw busy rejection, failure, then retry; worker timeout injected; browser recovered after a runtime error. |

Real wall-clock killing of a nonterminating program was not run separately; the timeout result path is tested by injection. No public deployment or multi-tab concurrency test is claimed.
