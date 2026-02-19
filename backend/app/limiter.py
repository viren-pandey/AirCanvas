from __future__ import annotations

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])
    slowapi_available = True
except ImportError:  # pragma: no cover - optional runtime dependency

    class _NoopLimiter:
        def limit(self, _rule: str):
            def decorator(func):
                return func

            return decorator

    limiter = _NoopLimiter()
    slowapi_available = False
