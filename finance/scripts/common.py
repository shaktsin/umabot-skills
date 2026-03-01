from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Tuple


def load_request() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}, {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        return {}, {}
    req_input = payload.get("input") if isinstance(payload.get("input"), dict) else {}
    req_cfg = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    return req_input, req_cfg


def get_api_key() -> str:
    key = os.environ.get("SERPAPI_API_KEY", "").strip()
    if not key:
        emit_error("SERPAPI_API_KEY environment variable is not set.")
    return key


def emit_ok(message: str, **data: Any) -> None:
    payload = {"ok": True, "message": message}
    payload.update(data)
    print(json.dumps(payload, ensure_ascii=True))


def emit_error(message: str, code: int = 1) -> None:
    print(json.dumps({"ok": False, "message": message}, ensure_ascii=True))
    sys.exit(code)
