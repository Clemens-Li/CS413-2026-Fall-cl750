"""Flask entry point for the LAMBDA3 JSON-RPC service."""

import multiprocessing

from .jsonrpc import create_app

app = create_app()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app.run(host="127.0.0.1", port=8000, use_reloader=False)
