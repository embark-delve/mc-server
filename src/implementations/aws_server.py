"""Cloud support is disabled pending a separate security and integration review."""

from typing import Any


class AWSServer:
    def __init__(self, **kwargs: Any) -> None:
        raise NotImplementedError("AWS is disabled. Use the local Docker backend")
