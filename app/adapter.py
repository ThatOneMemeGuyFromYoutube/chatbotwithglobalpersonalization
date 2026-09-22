from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from .config import settings
from .database import latest_adapter

_cached: dict[str, Any] | None = None
_cached_at = 0.0

def get_global_personality(db: Session) -> dict[str, Any]:
    global _cached, _cached_at
    now = time.time()
    if _cached is None or now - _cached_at >= settings.adapter_cache_seconds:
        _cached = latest_adapter(db)
        _cached_at = now
    return _cached
