"""JSON-RPC 2.0 request validation, dispatch, and response construction."""

from __future__ import annotations

import json
import logging
import math
from typing import Any

from flask import Flask, Response, jsonify, request

from .lambda_service import (
    MAX_SOURCE_CHARACTERS,
    ExecutionTimeout,
    LambdaService,
    LambdaSyntaxError,
    TypeCheckError,
)

logger = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 1_048_576


class RpcFault(Exception):
    def __init__(
        self,
        code: int,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def _error(
    code: int,
    message: str,
    request_id: Any = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "error": error, "id": request_id}


def _valid_id(value: Any) -> bool:
    if value is None or isinstance(value, str):
        return True
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return not isinstance(value, float) or math.isfinite(value)
    return False


def _validate_request(value: Any) -> tuple[bool, Any]:
    if not isinstance(value, dict):
        return False, None
    request_id = value.get("id")
    if (
        value.get("jsonrpc") != "2.0"
        or not isinstance(value.get("method"), str)
        or ("id" in value and not _valid_id(request_id))
    ):
        return False, None
    return True, request_id


def _params_object(params: Any) -> dict[str, Any]:
    if not isinstance(params, dict):
        raise RpcFault(-32602, "Invalid params")
    return params


def _source_parameter(params: dict[str, Any]) -> str:
    source = params.get("source")
    if not isinstance(source, str) or not source.strip():
        raise RpcFault(-32602, "Invalid params")
    if len(source) > MAX_SOURCE_CHARACTERS:
        raise RpcFault(
            -32602,
            "Invalid params",
            {"max_source_characters": MAX_SOURCE_CHARACTERS},
        )
    return source


def _dispatch(method: str, params: Any, service: LambdaService) -> Any:
    if method not in {
        "service.health",
        "lambda.typecheck",
        "lambda.interpret",
        "lambda.compile",
    }:
        raise RpcFault(-32601, "Method not found")

    arguments = _params_object(params)
    if method == "service.health":
        if arguments:
            raise RpcFault(-32602, "Invalid params")
        return {"status": "ok", "version": "1.0"}

    if method in {"lambda.typecheck", "lambda.interpret"}:
        if set(arguments) != {"source"}:
            raise RpcFault(-32602, "Invalid params")
        source = _source_parameter(arguments)
        if method == "lambda.typecheck":
            return service.typecheck(source)
        return service.interpret(source)

    if method == "lambda.compile":
        if set(arguments) != {"source", "target"}:
            raise RpcFault(-32602, "Invalid params")
        source = _source_parameter(arguments)
        target = arguments.get("target")
        if not isinstance(target, str) or target not in {"python", "javascript"}:
            raise RpcFault(-32602, "Invalid params")
        return service.compile(source, target)

    raise RpcFault(-32601, "Method not found")


def _handle_item(value: Any, service: LambdaService) -> tuple[dict[str, Any], bool]:
    valid, request_id = _validate_request(value)
    if not valid:
        return _error(-32600, "Invalid Request"), False

    is_notification = "id" not in value
    try:
        result = _dispatch(value["method"], value.get("params"), service)
        response = {"jsonrpc": "2.0", "result": result, "id": request_id}
    except RpcFault as fault:
        response = _error(fault.code, fault.message, request_id, fault.data)
    except LambdaSyntaxError as error:
        response = _error(
            -32010,
            "LAMBDA syntax error",
            request_id,
            {"diagnostic": str(error)},
        )
    except TypeCheckError as error:
        response = _error(
            -32011,
            "LAMBDA type-check error",
            request_id,
            {"diagnostic": str(error)},
        )
    except ExecutionTimeout as error:
        response = _error(
            -32012,
            "Execution timed out",
            request_id,
            {"timeout_seconds": error.timeout_seconds},
        )
    except Exception:
        logger.exception("Unexpected JSON-RPC backend failure")
        response = _error(-32603, "Internal error", request_id)
    return response, is_notification


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def create_app(service: LambdaService | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES
    lambda_service = service if service is not None else LambdaService()

    @app.errorhandler(413)
    def request_too_large(_error: Exception) -> tuple[Response, int]:
        _ = _error
        return jsonify({"error": "Request body too large"}), 413

    @app.post("/rpc")
    def rpc() -> Response | tuple[Response, int]:
        if request.mimetype != "application/json":
            return jsonify({"error": "Content-Type must be application/json"}), 415

        try:
            payload = json.loads(
                request.get_data(cache=False).decode("utf-8"),
                parse_constant=_reject_json_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return jsonify(_error(-32700, "Parse error")), 200

        if isinstance(payload, list):
            if not payload:
                return jsonify(_error(-32600, "Invalid Request")), 200
            responses = []
            for item in payload:
                response, is_notification = _handle_item(item, lambda_service)
                if not is_notification:
                    responses.append(response)
            if not responses:
                return Response(status=204)
            return jsonify(responses), 200

        response, is_notification = _handle_item(payload, lambda_service)
        if is_notification:
            return Response(status=204)
        return jsonify(response), 200

    return app
