# LAMBDA3 JSON-RPC service

A local HTTP JSON-RPC 2.0 wrapper around the provided LAMBDA3 parser,
type-checker, interpreter, and Python/JavaScript compilers.

## Requirements and setup

- Python 3.12 or later (verified with Python 3.14.2)
- Flask 3.1
- The sibling `LAMBDA3/` directory supplied with Assign07

From the `assigns/07/` directory, install dependencies and start the service:

```powershell
python -m pip install -r MySolution/requirements.txt
python -m MySolution.app
```

The server listens locally at `http://127.0.0.1:8000/rpc`. It exposes only
`POST /rpc`, with `Content-Type: application/json`. To run the automated tests
from the same `assigns/07/` directory:

```powershell
python -m unittest discover -s MySolution/tests -v
python -m unittest discover -s TEST -v
```

The second command is the assignment's black-box HTTP suite; start the service
in another terminal first. Set `LAMBDA_RPC_URL` if the server uses another
address.

## RPC examples

All examples use PowerShell's `curl.exe`; the service returns JSON-RPC
response objects with HTTP 200 for RPC outcomes. Replace the JSON body with
one of the examples below.

Health:

```powershell
curl.exe -sS http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-raw '{"jsonrpc":"2.0","method":"service.health","params":{},"id":"health"}'
```

Type-check:

```powershell
curl.exe -sS http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-raw '{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"1 + 2"},"id":1}'
```

Interpret factorial (expected result: `720`):

```powershell
curl.exe -sS http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-raw '{"jsonrpc":"2.0","method":"lambda.interpret","params":{"source":"let fact : sint -> sint = fix fact(n: sint): sint => if n <= 1 then 1 else n * fact(n - 1) in fact(6) end"},"id":"factorial"}'
```

An unbound variable is a LAMBDA type-check error (`-32011`):

```powershell
curl.exe -sS http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-raw '{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"missing_name"},"id":"unbound"}'
```

Compile to Python:

```powershell
curl.exe -sS http://127.0.0.1:8000/rpc -H "Content-Type: application/json" --data-raw '{"jsonrpc":"2.0","method":"lambda.compile","params":{"source":"1 + 2","target":"python"},"id":"compile"}'
```

Use `"target":"javascript"` for JavaScript output. The service returns
generated source code as text; it does not run the generated program.

## Limits and behavior

Client source is limited to 65,536 Unicode characters. Request bodies are
limited to 1 MiB. Interpretation runs in a separate process with a 2-second
deadline; if exceeded, the process is stopped and the RPC error is `-32012`.
A timeout indicates the deadline elapsed, not that the program is
nonterminating. The worker raises its recursion ceiling so Python's default
recursion limit does not preempt the wall-clock deadline. LAMBDA3's standard
library declarations from `LAMBDA3/mylib/` are available when source
expressions reference them.

JSON-RPC outcomes, including malformed JSON and invalid requests, use HTTP
200. Transport failures use HTTP statuses: unsupported media type is 415,
oversized request body is 413, and notifications return an empty response
with 204. See [RPC.md](./RPC.md) for the complete contract and
[RPC.schema.json](./RPC.schema.json) for the envelope schema.
