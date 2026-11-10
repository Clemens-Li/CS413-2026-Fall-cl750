import unittest

from MySolution.app import create_app
from MySolution.lambda_service import (
    INTERPRETATION_TIMEOUT_SECONDS,
    LambdaService,
    lambda3,
)


def call(method, params, request_id="test-id"):
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id,
    }


class RpcHttpTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def post(self, payload):
        return self.client.post("/rpc", json=payload)

    def assert_result(self, response, request_id, result):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id,
        })

    def assert_error(self, response, request_id, code):
        self.assertEqual(response.status_code, 200)
        body = response.json
        self.assertEqual(body["jsonrpc"], "2.0")
        self.assertEqual(body["id"], request_id)
        self.assertEqual(body["error"]["code"], code)
        self.assertNotIn("result", body)
        return body["error"]

    def test_health_and_typecheck(self):
        self.assert_result(
            self.post(call("service.health", {}, "health")),
            "health",
            {"status": "ok", "version": "1.0"},
        )
        self.assert_result(
            self.post(call("lambda.typecheck", {"source": "1 + 2"})),
            "test-id",
            {"type": "sint"},
        )
        self.assert_result(
            self.post(call("service.health", {}, None)),
            None,
            {"status": "ok", "version": "1.0"},
        )

    def test_interpret_arithmetic_factorial_tuple_and_list(self):
        programs = (
            ("20 + 22", {"type": "sint", "value": "42"}),
            (
                "let fact : sint -> sint = fix fact(n: sint): sint => "
                "if n <= 1 then 1 else n * fact(n - 1) in fact(6) end",
                {"type": "sint", "value": "720"},
            ),
            ("(1, true)", {"type": "(sint, bool)", "value": "(1, true)"}),
            (
                "list_cons(1, list_cons(2, list_nil()))",
                {"type": "List[sint]", "value": "[1, 2]"},
            ),
            (
                "list_length(list_cons(7, list_cons(8, list_nil())))",
                {"type": "sint", "value": "2"},
            ),
        )
        for source, expected in programs:
            with self.subTest(source=source):
                self.assert_result(
                    self.post(call("lambda.interpret", {"source": source})),
                    "test-id",
                    expected,
                )

    def test_function_value_hides_closure(self):
        source = "let f : sint -> sint = lam (x: sint) => x in f end"
        response = self.post(call("lambda.interpret", {"source": source}))
        self.assert_result(
            response,
            "test-id",
            {"type": "sint -> sint", "value": "<lam>"},
        )
        self.assertNotIn("environment", response.json["result"]["value"])

    def test_interpreter_runtime_failure_is_masked(self):
        response = self.post(
            call("lambda.interpret", {"source": "1 / 0"}, "runtime-failure")
        )
        error = self.assert_error(response, "runtime-failure", -32603)
        self.assertEqual(error["message"], "Internal error")
        self.assertNotIn("division by zero", str(error).lower())
        self.assertNotIn("traceback", str(error).lower())

    def test_compile_python_and_javascript(self):
        expression, _ = lambda3.d0exp_parse_and_typecheck("1 + 2")
        for target in ("python", "javascript"):
            with self.subTest(target=target):
                response = self.post(call(
                    "lambda.compile",
                    {"source": "1 + 2", "target": target},
                ))
                self.assertEqual(response.status_code, 200)
                result = response.json["result"]
                self.assertEqual(result["target"], target)
                self.assertTrue(result["code"].strip())
                compiler = (
                    lambda3.d0exp_compile
                    if target == "python"
                    else lambda3.d0exp_compile_js
                )
                self.assertEqual(result["code"], compiler(expression))

        library_response = self.post(call(
            "lambda.compile",
            {
                "source": "list_length(list_cons(1, list_nil()))",
                "target": "python",
            },
        ))
        self.assertEqual(library_response.status_code, 200)
        self.assertTrue(library_response.json["result"]["code"].strip())

    def test_syntax_type_and_unbound_variable_errors(self):
        syntax_error = self.assert_error(
            self.post(call("lambda.typecheck", {"source": "if then"})),
            "test-id",
            -32010,
        )
        type_error = self.assert_error(
            self.post(call("lambda.typecheck", {"source": "1 + true"})),
            "test-id",
            -32011,
        )
        unbound_error = self.assert_error(
            self.post(call("lambda.typecheck", {"source": "not_bound"})),
            "test-id",
            -32011,
        )
        self.assertIn("diagnostic", syntax_error["data"])
        self.assertIn("diagnostic", type_error["data"])
        self.assertEqual(type_error["data"]["diagnostic"], "+: expected bool, got sint")
        self.assertIn("not_bound", unbound_error["data"]["diagnostic"])
        self.assertNotIn("\\", unbound_error["data"]["diagnostic"])
        self.assertNotIn("/", unbound_error["data"]["diagnostic"])

    def test_invalid_params_and_unknown_method(self):
        self.assert_error(
            self.post(call("lambda.interpret", {"source": "  "})),
            "test-id",
            -32602,
        )
        self.assert_error(
            self.post(call("lambda.interpret", {"source": 10})),
            "test-id",
            -32602,
        )
        self.assert_error(
            self.post(call("lambda.interpret", None)),
            "test-id",
            -32602,
        )
        self.assert_error(
            self.post(call("lambda.compile", {"source": "1", "target": []})),
            "test-id",
            -32602,
        )
        self.assert_error(
            self.post(call("lambda.compile", {"source": "1", "target": "ruby"})),
            "test-id",
            -32602,
        )
        self.assert_error(
            self.post(call("missing.method", {})),
            "test-id",
            -32601,
        )
        self.assert_error(
            self.post({
                "jsonrpc": "2.0",
                "method": "missing.method",
                "id": "unknown-without-params",
            }),
            "unknown-without-params",
            -32601,
        )
        self.assert_error(
            self.post({
                "jsonrpc": "2.0",
                "method": "service.health",
                "id": "missing-params",
            }),
            "missing-params",
            -32602,
        )
        self.assert_error(
            self.post(call("service.health", {"extra": True})),
            "test-id",
            -32602,
        )
        self.assert_error(
            self.post(call("lambda.typecheck", ["1 + 2"])),
            "test-id",
            -32602,
        )
        self.assert_error(
            self.post(call("lambda.typecheck", {
                "source": "x" * 65_537,
            })),
            "test-id",
            -32602,
        )

    def test_parse_invalid_request_and_transport_errors(self):
        malformed = self.client.post(
            "/rpc",
            data=b'{"jsonrpc":',
            content_type="application/json",
        )
        self.assert_error(malformed, None, -32700)
        for payload in (
            {"jsonrpc": "1.0", "method": "service.health", "id": 1},
            {"jsonrpc": "2.0", "method": "service.health", "id": True},
            "not an object",
        ):
            with self.subTest(payload=payload):
                self.assert_error(self.post(payload), None, -32600)
        unsupported = self.client.post("/rpc", data="{}", content_type="text/plain")
        self.assertEqual(unsupported.status_code, 415)

    def test_notifications_and_batches(self):
        notification = {
            "jsonrpc": "2.0",
            "method": "service.health",
            "params": {},
        }
        single = self.post(notification)
        self.assertEqual(single.status_code, 204)
        self.assertEqual(single.data, b"")

        mixed = self.post([
            call("lambda.interpret", {"source": "6 * 7"}, "answer"),
            notification,
            "invalid-item",
        ])
        self.assertEqual(mixed.status_code, 200)
        self.assertEqual(len(mixed.json), 2)
        self.assertEqual(mixed.json[0]["id"], "answer")
        self.assertEqual(mixed.json[0]["result"]["value"], "42")
        self.assertEqual(mixed.json[1]["id"], None)
        self.assertEqual(mixed.json[1]["error"]["code"], -32600)

        only_notifications = self.post([notification, notification])
        self.assertEqual(only_notifications.status_code, 204)
        self.assertEqual(only_notifications.data, b"")
        self.assert_error(self.post([]), None, -32600)

    def test_interpretation_timeout_is_explicit(self):
        app = create_app(LambdaService())
        source = (
            "let loop : sint -> sint = "
            "fix loop(n: sint): sint => loop(n) in loop(0) end"
        )
        response = app.test_client().post(
            "/rpc",
            json=call("lambda.interpret", {"source": source}, "slow"),
        )
        error = self.assert_error(response, "slow", -32012)
        self.assertEqual(
            error["data"]["timeout_seconds"],
            INTERPRETATION_TIMEOUT_SECONDS,
        )
        self.assertNotIn("traceback", str(error).lower())

    def test_unexpected_failure_is_masked(self):
        class FailingService:
            timeout_seconds = 2.0

            def typecheck(self, _source):
                self_source = _source
                if self_source != "1 + 2":
                    raise AssertionError("Unexpected typecheck source")
                raise RuntimeError("private backend detail")

        response = create_app(FailingService()).test_client().post(
            "/rpc",
            json=call("lambda.typecheck", {"source": "1 + 2"}, "failure"),
        )
        error = self.assert_error(response, "failure", -32603)
        self.assertNotIn("private backend detail", str(error))
        self.assertNotIn("traceback", str(error).lower())

    def test_oversized_http_body_uses_transport_status(self):
        response = self.client.post(
            "/rpc",
            data=" " * (1_048_577),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
