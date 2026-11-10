# AI usage transcript

AI assistance was used while implementing this assignment. The tool was an AI
assistant using Copilot SDK in VS Code.

## Important prompts and suggestions

- The task requested a thorough reading of `Assign07.md`, incremental
  implementation, correctness checks, full functionality testing, and
  debugging.
- The implementation followed the assignment's specified ordering by writing
  the RPC contract before the dispatcher, then adding the LAMBDA3 adapter,
  HTTP dispatcher, tests, and usage documentation.
- Inspection showed that the provided `LAMBDA3/mylib/*.lam` files contain
  sequential declarations; they were included as a LAMBDA3 `let` prelude so
  library functions can be used by RPC source programs.
- An initial test run exposed a missing `return app` in the Flask factory.
  The test suite also checks batch invalid-member handling, notification
  behavior, deadlines, request size, and generic backend failures.

## Review and testing

The result was reviewed against the assignment's endpoint, request/response
envelopes, error mapping, source and time limits, and method behavior. It was
validated with the in-process HTTP suite in `tests/test_rpc.py`, Python syntax
checks, JSON Schema parsing, and the provided black-box suite in `../TEST/`.
A later correctness pass confirmed the live contract suite, then changed
standard-library loading to wrap a parsed `D0Elets` AST (the form `mylib`
documents) instead of concatenating library source into the client program.
An edge-case probe found recursive LAMBDA loops reaching CPython's recursion
limit before the worker deadline; the worker recursion ceiling was raised so
the parent deadline can terminate such evaluations. The timeout test now uses
an actual recursive loop, and compiler tests compare returned code byte for
byte with the LAMBDA3 compiler output.
See [TESTING.md](./TESTING.md) for the test-to-requirement mapping and observed
results.
