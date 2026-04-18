from typing import Any


def success_response(data: Any = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": True,
        "data": data if data is not None else {},
        "meta": meta or {},
        "error": None,
    }
