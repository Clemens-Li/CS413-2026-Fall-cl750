# LAMBDA3 JSON-RPC contract

## Transport and envelope

Send UTF-8 JSON with `Content-Type: application/json` to `POST /rpc`. This
local-development service returns JSON-RPC outcomes with HTTP 200, including
parse, invalid-request, and application errors. HTTP statuses describe
transport handling: unsupported media types use 415, oversized HTTP bodies
use 413, and an absent response (a notification) uses 204 with an empty body.
The response media type is `application/json` when a response body is present.

Each call has `"jsonrpc": "2.0"`, a string `method`, and an object `params`.
The supported methods require an `id` that is a string, number, or null;
omitting it makes the request a notification. A present null ID is a call and
receives a response with `"id": null`. Boolean and structured IDs are invalid.
Responses echo usable IDs and contain exactly one of `result` or `error`.
Clients must match batch responses by ID, not array order. Invalid items
receive an Invalid Request response with a null ID. An empty batch returns one
Invalid Request object rather than an array. A nonempty batch returns an array
of responses, omitting notifications; an all-notification batch returns 204
and no body.

The service accepts request bodies up to 1 MiB and source strings up to
65,536 Unicode characters. Exceeding the source limit is Invalid params.
Interpretation runs in a separate worker process with a 2-second execution
deadline; the process is terminated on expiry. The worker allows recursive
evaluations to proceed beyond CPython's usual recursion ceiling so the wall
clock deadline, rather than a shallow interpreter stack limit, can stop long
computations. A timeout only means the deadline elapsed, not that the
expression is nonterminating.

## Methods

| Method | Parameters | Result | Behavior |
| --- | --- | --- | --- |
| `service.health` | `{}` | `{"status":"ok","version":"1.0"}` | Reports service/API status. |
| `lambda.typecheck` | `{"source":"..."}` | `{"type":"sint"}` | Parses and type-checks LAMBDA3 source. |
| `lambda.interpret` | `{"source":"..."}` | `{"type":"sint","value":"42"}` | Parses and type-checks, then evaluates in a deadline-limited worker. Values are formatted strings. |
| `lambda.compile` | `{"source":"...","target":"python"}` or `{"source":"...","target":"javascript"}` | `{"target":"python","code":"..."}` | Parses and type-checks, then returns compiler output unchanged. Generated code is not executed. |

All source operations require nonblank source. Compile targets are case
sensitive. The LAMBDA3 standard library under `LAMBDA3/mylib/` is part of the
provided language distribution; service methods consume expressions in the
LAMBDA3 language, not Python constructor expressions.

## Error mapping

Error objects contain integer `code`, string `message`, and optional
structured `data`. `data` is omitted when no additional client-safe detail is
available.

| Condition | Code | Message/data |
| --- | ---: | --- |
| Malformed JSON body | `-32700` | `Parse error`; no parser details. |
| Malformed JSON-RPC envelope, invalid ID, or empty batch | `-32600` | `Invalid Request`. |
| Unsupported method | `-32601` | `Method not found`. |
| Missing/wrong params, blank source, unsupported target, or oversized source | `-32602` | `Invalid params`; oversized source includes `{"max_source_characters":65536}`. |
| LAMBDA3 syntax error | `-32010` | `LAMBDA syntax error`; `data.diagnostic` contains a client-safe parser diagnostic. |
| LAMBDA3 type-check error (including unbound variables) | `-32011` | `LAMBDA type-check error`; `data.diagnostic` contains the type-check diagnostic. |
| Interpretation deadline exceeded | `-32012` | `Execution timed out`; `data.timeout_seconds` is `2`. |
| Unexpected server/backend or unclassified interpreter failure | `-32603` | `Internal error`; details are logged server-side and never returned. |

LAMBDA3 source syntax errors are application errors, not JSON-RPC parse
errors. Tracebacks and filesystem paths are not returned to clients.

## Examples

### Health

Request:

```json
{"jsonrpc":"2.0","method":"service.health","params":{},"id":"health-1"}
```

Response:

```json
{"jsonrpc":"2.0","result":{"status":"ok","version":"1.0"},"id":"health-1"}
```

### Type-check

Request:

```json
{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"1 + 2"},"id":2}
```

Response:

```json
{"jsonrpc":"2.0","result":{"type":"sint"},"id":2}
```

### Interpretation

Request:

```json
{"jsonrpc":"2.0","method":"lambda.interpret","params":{"source":"20 + 22"},"id":3}
```

Response:

```json
{"jsonrpc":"2.0","result":{"type":"sint","value":"42"},"id":3}
```

### Compilation

Request:

```json
{"jsonrpc":"2.0","method":"lambda.compile","params":{"source":"1 + 2","target":"javascript"},"id":4}
```

Complete response (the `code` field is the exact generated source string):

```json
{"jsonrpc":"2.0","result":{"target":"javascript","code":"const _lambda_some_tag = Symbol(\"some\");\nconst _lambda_tuple_tag = Symbol(\"tuple\");\nconst _lambda_lazy_tag = Symbol(\"lazy\");\nconst _lambda_stcn_tag = Symbol(\"stcn\");\n\nfunction _lambda_list_cons(head, tail) {\n  if (!Array.isArray(tail)) throw new TypeError(\"list_cons: list tail expected\");\n  return [head, ...tail];\n}\nfunction _lambda_list_nilq(value) {\n  if (!Array.isArray(value)) throw new TypeError(\"list_nilq: list expected\");\n  return value.length === 0;\n}\nfunction _lambda_list_head(value) {\n  if (!Array.isArray(value)) throw new TypeError(\"list_head: list expected\");\n  if (!value.length) throw new Error(\"list_head: nonempty list expected\");\n  return value[0];\n}\nfunction _lambda_list_tail(value) {\n  if (!Array.isArray(value)) throw new TypeError(\"list_tail: list expected\");\n  if (!value.length) throw new Error(\"list_tail: nonempty list expected\");\n  return value.slice(1);\n}\nfunction _lambda_a1sz_index(array, index) {\n  if (!Array.isArray(array) || !Number.isInteger(index)) throw new TypeError(\"A1sz indexing expects an array and integer index\");\n  if (index < 0 || index >= array.length) throw new RangeError(\"A1sz index out of range\");\n  return index;\n}\nfunction _lambda_a1sz_getat(array, index) { return array[_lambda_a1sz_index(array, index)]; }\nfunction _lambda_a1sz_setat(array, index, value) { array[_lambda_a1sz_index(array, index)] = value; return _lambda_tuple([]); }\nfunction _lambda_a1sz_make_ncpy(size, value) {\n  if (!Number.isInteger(size)) throw new TypeError(\"A1sz size must be sint\");\n  if (size < 0) throw new RangeError(\"A1sz size must be nonnegative\");\n  return Array(size).fill(value);\n}\nfunction _lambda_a1sz_make_nfun(size, fn) {\n  if (!Number.isInteger(size)) throw new TypeError(\"A1sz size must be sint\");\n  if (size < 0) throw new RangeError(\"A1sz size must be nonnegative\");\n  return Array.from({length: size}, (_, i) => fn(i));\n}\nfunction _lambda_tuple(items) { return { tag: _lambda_tuple_tag, items }; }\nfunction _lambda_tuple_get(value, index) {\n  if (!value || value.tag !== _lambda_tuple_tag)\n    throw new TypeError(\"tuple projection: tuple expected\");\n  return value.items[index];\n}\nfunction _lambda_optn_cons(value) { return { tag: _lambda_some_tag, value }; }\nfunction _lambda_optn_nilq(value) { return value === null; }\nfunction _lambda_optn_get(value) {\n  if (value === null || value.tag !== _lambda_some_tag)\n    throw new Error(\"optn_get: nonempty option expected\");\n  return value.value;\n}\nfunction _lambda_lazy_make(thunk) {\n  if (typeof thunk !== \"function\") throw new TypeError(\"lazy_make: thunk function expected\");\n  return { tag: _lambda_lazy_tag, thunk, evaluated: false, value: undefined };\n}\nfunction _lambda_lazy_eval(value) {\n  if (!value || value.tag !== _lambda_lazy_tag) throw new TypeError(\"lazy_eval: Lazy value expected\");\n  if (!value.evaluated) {\n    value.value = value.thunk(_lambda_tuple([]));\n    value.evaluated = true;\n  }\n  return value.value;\n}\nfunction _lambda_stcn_nil() { return { tag: _lambda_stcn_tag, cons: false }; }\nfunction _lambda_stcn_cons(head, tail) {\n  if (!tail || tail.tag !== _lambda_lazy_tag) throw new TypeError(\"stcn_cons: lazy stream tail expected\");\n  return { tag: _lambda_stcn_tag, cons: true, head, tail };\n}\nfunction _lambda_stcn_check(value, name) {\n  if (!value || value.tag !== _lambda_stcn_tag) throw new TypeError(name + \": Stcn value expected\");\n}\nfunction _lambda_stcn_nilq(value) { _lambda_stcn_check(value, \"stcn_nilq\"); return !value.cons; }\nfunction _lambda_stcn_consq(value) { _lambda_stcn_check(value, \"stcn_consq\"); return value.cons; }\nfunction _lambda_stcn_head(value) {\n  _lambda_stcn_check(value, \"stcn_head\");\n  if (!value.cons) throw new Error(\"stcn_head: nonempty stream constructor expected\");\n  return value.head;\n}\nfunction _lambda_stcn_tail(value) {\n  _lambda_stcn_check(value, \"stcn_tail\");\n  if (!value.cons) throw new Error(\"stcn_tail: nonempty stream constructor expected\");\n  return value.tail;\n}\nfunction _lambda_format(value) {\n  if (value && value.tag === _lambda_lazy_tag) return \"<lazy>\";\n  if (value && value.tag === _lambda_stcn_tag) {\n    if (!value.cons) return \"stcn_nil()\";\n    return \"stcn_cons(\" + _lambda_format(value.head) + \", <lazy>)\";\n  }\n  if (value === null) return \"optn_nil()\";\n  if (value && value.tag === _lambda_some_tag)\n    return \"optn_cons(\" + _lambda_format(value.value) + \")\";\n  if (typeof value === \"boolean\") return value ? \"true\" : \"false\";\n  if (Array.isArray(value)) return \"[\" + value.map(_lambda_format).join(\", \") + \"]\";\n  if (value && value.tag === _lambda_tuple_tag) {\n    const body = value.items.map(_lambda_format).join(\", \");\n    return \"(\" + body + (value.items.length === 1 ? \",\" : \"\") + \")\";\n  }\n  if (typeof value === \"function\") return \"<lam>\";\n  return String(value);\n}\nfunction _lambda_print(value) { console.log(_lambda_format(value)); return _lambda_tuple([]); }\n\nfunction _lambda_main() {\n  let _v1 = 1;\n  let _v2 = 2;\n  let _v3 = (_v1 + _v2);\n  return _v3;\n}\nconst _lambda_result = _lambda_main();\n"},"id":4}
```

### Syntax error

Request:

```json
{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"if then"},"id":"syntax"}
```

Response:

```json
{"jsonrpc":"2.0","error":{"code":-32010,"message":"LAMBDA syntax error","data":{"diagnostic":"Expected an expression (<lambda>, line 1)"}},"id":"syntax"}
```

### Type error

Request:

```json
{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"1 + true"},"id":"type"}
```

Response:

```json
{"jsonrpc":"2.0","error":{"code":-32011,"message":"LAMBDA type-check error","data":{"diagnostic":"+: expected bool, got sint"}},"id":"type"}
```

### Batch with calls and a notification

Request:

```json
[{"jsonrpc":"2.0","method":"lambda.interpret","params":{"source":"6 * 7"},"id":"answer"},{"jsonrpc":"2.0","method":"service.health","params":{}}]
```

Response (the notification has no response):

```json
[{"jsonrpc":"2.0","result":{"type":"sint","value":"42"},"id":"answer"}]
```

### Notification-only batch

Request:

```json
[{"jsonrpc":"2.0","method":"service.health","params":{}},{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"1 + 2"}}]
```

Response: HTTP 204 with an empty body.

## Envelope schema

The companion [JSON Schema](./RPC.schema.json) describes request objects,
notifications, batch payloads, and success/error response envelopes. The
schema cannot express the conditional notification rule or method-specific
params; those are enforced by the dispatcher.
