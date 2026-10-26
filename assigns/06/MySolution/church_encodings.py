"""Import-safe public name for the Church encoding library.

The original assignment file is retained as ``encodings.py`` for backwards
compatibility, but that basename conflicts with Python's standard-library
``encodings`` package when this directory is put on ``sys.path``.  New code
uses this module instead.
"""
from __future__ import annotations

import importlib.util
import pathlib

_path = pathlib.Path(__file__).with_name("encodings.py")
_spec = importlib.util.spec_from_file_location("_assignment6_encodings", _path)
_module = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_module)

for _name in _module.__all__:
    globals()[_name] = getattr(_module, _name)
__all__ = _module.__all__
