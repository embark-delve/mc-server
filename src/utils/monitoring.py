"""Persistent metrics are disabled. Use server status and Docker resource tools."""

from typing import Any


class ServerMonitor:
    def __init__(self, **kwargs: Any) -> None:
        raise NotImplementedError(
            "Persistent monitoring is disabled; no metrics listener is started"
        )
