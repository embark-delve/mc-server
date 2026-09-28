"""The former ephemeral idle monitor is disabled instead of claiming protection."""

from typing import Any


class AutoShutdown:
    def __init__(self, **kwargs: Any) -> None:
        raise NotImplementedError(
            "Use explicit server stop; automatic shutdown is not supported"
        )
