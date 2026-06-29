"""Error types for StableOps SDK."""

from typing import Any, Optional


class StableOpsError(Exception):
    """Base exception for StableOps SDK errors."""

    def __init__(
        self,
        message: str,
        status: int = 0,
        code: str = "unknown_error",
        details: Optional[Any] = None,
    ) -> None:
        """Initialize StableOpsError.

        Args:
            message: Error message
            status: HTTP status code (0 for network errors)
            code: Error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details

    def __str__(self) -> str:
        """String representation."""
        if self.status > 0:
            return f"[{self.status}] {self.code}: {self.message}"
        return f"{self.code}: {self.message}"

    def __repr__(self) -> str:
        """Repr representation."""
        return (
            f"StableOpsError(message={self.message!r}, status={self.status}, "
            f"code={self.code!r}, details={self.details!r})"
        )
