if __name__ == "__main__":
    from MySolution.jsonrpc import create_app

    client = create_app().test_client()
    cases = {
        "div0": {
            "jsonrpc": "2.0",
            "method": "lambda.interpret",
            "params": {"source": "1 / 0"},
            "id": "div0",
        },
        "print": {
            "jsonrpc": "2.0",
            "method": "lambda.interpret",
            "params": {"source": "print(1)"},
            "id": "print",
        },
        "strm": {
            "jsonrpc": "2.0",
            "method": "lambda.interpret",
            "params": {"source": "strm_head(strm_cons((1, strm_nil(()))))"},
            "id": "strm",
        },
        "timeout-loop": {
            "jsonrpc": "2.0",
            "method": "lambda.interpret",
            "params": {
                "source": (
                    "let loop : sint -> sint = "
                    "fix loop(n: sint): sint => loop(n) in loop(0) end"
                )
            },
            "id": "loop",
        },
        "missing params compile": {
            "jsonrpc": "2.0",
            "method": "lambda.compile",
            "params": {"source": "1"},
            "id": "no-target",
        },
        "null id health": {
            "jsonrpc": "2.0",
            "method": "service.health",
            "params": {},
            "id": None,
        },
    }
    for name, payload in cases.items():
        response = client.post("/rpc", json=payload)
        print(name, response.status_code, response.json)
