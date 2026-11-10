# Testing

Run both HTTP test suites from the `assigns/07/` directory. The in-process
suite uses Flask's HTTP test client; the assignment black-box suite requires
the server at `http://127.0.0.1:8000/rpc` to be running.

```powershell
python -m unittest discover -s MySolution/tests -v
python -m unittest discover -s TEST -v
```

## Architecture

```text
HTTP POST /rpc (Flask)
          |
          v
JSON-RPC envelope validation, dispatch, and response mapping
          |
          v
LAMBDA3 service adapter -- parse/type-check, format, compile
          |                             |
          | interpretation              +--> d0exp_compile / d0exp_compile_js
          v
Terminable worker process
          |
          v
LAMBDA3 module + declarations loaded from LAMBDA3/mylib/*.lam
```

## Requirement-to-test mapping

| Required behavior | Test coverage |
| --- | --- |
| Health status, API version, and request ID | `test_health_and_typecheck`; black-box `test_health` |
| LAMBDA3 type-checking | `test_health_and_typecheck`, `test_syntax_type_and_unbound_variable_errors`; black-box `test_typecheck_arithmetic` |
| Arithmetic, factorial, tuple, collection, and standard library | `test_interpret_arithmetic_factorial_tuple_and_list`; black-box `test_interpret_arithmetic`, `test_interpret_tuple`, `test_interpret_list` |
| Python and JavaScript compilation | `test_compile_python_and_javascript`; black-box `test_compile_python_and_javascript` |
| Distinct syntax/type errors and unbound-variable rejection | `test_syntax_type_and_unbound_variable_errors`; black-box `test_language_syntax_and_type_errors_are_distinct` |
| Malformed JSON, invalid envelope/ID, params, blank/oversized source, unknown method | `test_invalid_params_and_unknown_method`, `test_parse_invalid_request_and_transport_errors`; black-box `test_invalid_params_and_unknown_method`, `test_malformed_json_returns_parse_error`, `test_invalid_request_and_empty_batch` |
| Function values do not expose closure state | `test_function_value_hides_closure`; black-box `test_interpret_function_formats_closure` |
| Backend and interpreter failures masked; deadline error preserves ID | `test_unexpected_failure_is_masked`, `test_interpreter_runtime_failure_is_masked`, `test_interpretation_timeout_is_explicit` |
| Batch IDs, omitted notifications, invalid member, empty batch, 204 notifications | `test_notifications_and_batches`; black-box `test_batch_matches_by_id_and_omits_notification`, `test_notification_only_batch_has_no_response`, `test_notification_has_no_response`, `test_malformed_batch_member_gets_null_id_error` |
| Transport media/body limits | `test_parse_invalid_request_and_transport_errors`, `test_oversized_http_body_uses_transport_status` |

## Observed results

- In-process suite: **12 tests passed**.
- Python compilation check: **passed**.
- `RPC.schema.json` JSON parsing check: **passed**.
- Assignment black-box HTTP suite: **15 tests passed** against the live
  service at `127.0.0.1:8000/rpc`.
