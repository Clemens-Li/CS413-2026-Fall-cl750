# AI assistance record

Tools used: Cursor agent (Composer) while completing Assignment 04 in `assigns/04/MySolution/`.

## Important prompts and suggestions

1. Read `Assign04.md` and complete the application incrementally, then test thoroughly.
2. Earlier work in this directory had rebuilt a LAMBDA MVC workbench after a lost `Solution` tree; this session reviewed that tree against the assignment checklist.

## What the agent changed or verified

- Confirmed MVC modules (`model.py`, `controller.py`, `backend.py`, `app.py`) and the restricted constructor reader against the assignment contract.
- Restored the primary graded path: when the page is served by `app.py`, `static/app.js` uses HTTP `fetch` to the Python controller/model/backend instead of only the offline JavaScript worker.
- Kept the offline `file://` / static JavaScript port as a documented fallback with the same adapter outcomes.
- Updated `ARCHITECTURE.md` (placeholder replacement path), `README.md` (`MySolution` paths), and verification docs.
- Normalized example/test line-ending handling for Windows; pointed browser screenshot output at the OS temp directory.

A later prompt asked to continue according to `Assign04.md`. Remaining gaps were a sequence diagram in `ARCHITECTURE.md`, explicit browser step/expected/observed rows in `TESTING.md`, a 200–300 word reflection trim, and the required meaningful Git commits under `MySolution/`.

## Review and testing of AI output

- `python -m unittest discover -s tests -v` — 8/8 passed.
- `node tests/browser-runtime.cjs` — JS runtime, worker/controller slice, and Python parity passed.
- `python tests/http_smoke.py` against `http://127.0.0.1:8040` — 20/20 passed.
- `node --experimental-websocket tests/browser-smoke.mjs` with headless Chrome CDP — browser smoke checks passed; mobile overflow false.

Human review still owns grading judgment about architectural clarity and demonstration quality; automated checks cover the behavioral requirements listed in `TESTING.md`.
