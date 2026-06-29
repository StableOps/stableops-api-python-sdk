"""HTTP client with retry logic."""

import logging
import random
import time
from typing import Any, Callable, Dict, Literal, Mapping, Optional, Union
from urllib.parse import urlencode

try:
    from importlib.metadata import version as _pkg_version

    _SDK_VERSION = _pkg_version("stableops")
except Exception:
    _SDK_VERSION = "unknown"

import httpx

from stableops.errors import StableOpsError

IDEMPOTENCY_HEADER = "idempotency-key"

DEFAULT_BASE_URL = "https://api.stableops.dev"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_BASE_DELAY = 0.2
DEFAULT_MAX_DELAY = 5.0

HttpMethod = Literal["GET", "POST", "PATCH", "DELETE"]

# debug 钩子签名：接收一个 dict 事件（init / request / response / error）。
# 传 True 走 logging.getLogger("stableops") .debug；也可传任意可调用对象自行处理。
DebugCallback = Callable[[Dict[str, Any]], None]
DebugOption = Union[bool, DebugCallback, None]

_SENSITIVE_HEADERS = frozenset({"authorization", IDEMPOTENCY_HEADER, "cookie", "set-cookie"})

_logger = logging.getLogger("stableops")


def mask_secret(value: Optional[str]) -> Optional[str]:
    """Mask a secret, keeping first/last 4 chars when long enough."""
    if value is None:
        return None
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}***{value[-4:]}"


def _mask_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in headers.items():
        lower = k.lower()
        if lower in _SENSITIVE_HEADERS:
            if lower == "authorization" and v.startswith("Bearer "):
                masked = mask_secret(v[7:]) or "***"
                out[k] = f"Bearer {masked}"
            else:
                out[k] = mask_secret(v) or "***"
        else:
            out[k] = v
    return out


def _resolve_debug(option: DebugOption) -> Optional[DebugCallback]:
    if not option:
        return None
    if callable(option):
        return option

    def _default(event: Dict[str, Any]) -> None:
        _logger.debug("stableops %s", event)

    return _default


def is_retryable_status(status: int) -> bool:
    """Check if HTTP status is retryable."""
    return status == 429 or status >= 500


def is_retryable_error(error: Exception) -> bool:
    """Check if error is retryable."""
    if isinstance(error, httpx.TimeoutException):
        return True
    if isinstance(error, httpx.NetworkError):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        return is_retryable_status(error.response.status_code)
    return False


def compute_delay(
    attempt: int, base_delay: float, max_delay: float, retry_after: Optional[float] = None
) -> float:
    """Compute retry delay with exponential backoff and jitter."""
    if retry_after is not None:
        return min(retry_after, max_delay)

    # Exponential backoff: base_delay * 2^attempt
    delay = base_delay * (2**attempt)

    # Full jitter: random between 0 and delay
    delay = random.uniform(0, delay)

    return min(delay, max_delay)


class HttpClient:
    """Synchronous HTTP client with retry logic."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
        debug: DebugOption = None,
    ) -> None:
        """Initialize HTTP client.

        Args:
            api_key: API key for authentication
            base_url: Base API URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            base_delay: Base delay for exponential backoff
            max_delay: Maximum delay between retries
            debug: True 走 logging "stableops" logger，可调用对象则自行处理；
                敏感字段（api_key / authorization / idempotency-key 等）始终先脱敏。
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._debug = _resolve_debug(debug)

        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": f"StableOpsSDK/{_SDK_VERSION}",
        }
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"

        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
        )

        if self._debug:
            self._debug(
                {
                    "type": "init",
                    "config": {
                        "base_url": self.base_url,
                        "api_key": mask_secret(api_key),
                        "timeout": self.timeout,
                        "max_retries": self.max_retries,
                        "base_delay": self.base_delay,
                        "max_delay": self.max_delay,
                    },
                }
            )

    def request(
        self,
        method: HttpMethod,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method
            path: Request path
            body: Request body (JSON)
            query: Query parameters
            idempotency_key: Idempotency key for write operations

        Returns:
            Response JSON

        Raises:
            StableOpsError: On API error or network failure
        """
        url = path
        if query:
            # Filter out None values
            filtered_query = {k: v for k, v in query.items() if v is not None}
            if filtered_query:
                url = f"{path}?{urlencode(filtered_query)}"

        headers = {}
        if idempotency_key:
            headers[IDEMPOTENCY_HEADER] = idempotency_key

        for attempt in range(self.max_retries + 1):
            started = time.monotonic()
            if self._debug:
                merged = {**dict(self.client.headers), **headers}
                self._debug(
                    {
                        "type": "request",
                        "method": method,
                        "url": f"{self.base_url}{url}",
                        "headers": _mask_headers(merged),
                        "body": body,
                        "attempt": attempt,
                    }
                )
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    json=body,
                    headers=headers,
                )
                if self._debug:
                    self._debug(
                        {
                            "type": "response",
                            "method": method,
                            "url": f"{self.base_url}{url}",
                            "status": response.status_code,
                            "duration_ms": int((time.monotonic() - started) * 1000),
                            "headers": dict(response.headers),
                            "body": _safe_json(response),
                            "attempt": attempt,
                        }
                    )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                status = e.response.status_code

                # Don't retry 4xx errors (except 429)
                if 400 <= status < 500 and status != 429:
                    error_data = self._parse_error(e.response)
                    raise StableOpsError(
                        message=error_data.get("message", str(e)),
                        status=status,
                        code=error_data.get("code", "api_error"),
                        details=error_data.get("details"),
                    ) from e

                # Retry on 429 and 5xx
                if attempt < self.max_retries and is_retryable_status(status):
                    retry_after = self._parse_retry_after(e.response)
                    delay = compute_delay(attempt, self.base_delay, self.max_delay, retry_after)
                    time.sleep(delay)
                    continue

                # Max retries exceeded
                error_data = self._parse_error(e.response)
                raise StableOpsError(
                    message=error_data.get("message", str(e)),
                    status=status,
                    code=error_data.get("code", "api_error"),
                    details=error_data.get("details"),
                ) from e

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if self._debug:
                    self._debug(
                        {
                            "type": "error",
                            "method": method,
                            "url": f"{self.base_url}{url}",
                            "attempt": attempt,
                            "duration_ms": int((time.monotonic() - started) * 1000),
                            "error": {"type": type(e).__name__, "message": str(e)},
                        }
                    )
                # Retry on timeout and network errors
                if attempt < self.max_retries:
                    delay = compute_delay(attempt, self.base_delay, self.max_delay)
                    time.sleep(delay)
                    continue

                # Max retries exceeded
                error_type = "timeout" if isinstance(e, httpx.TimeoutException) else "network_error"
                raise StableOpsError(
                    message=str(e),
                    status=0,
                    code=error_type,
                    details=None,
                ) from e

        # Should never reach here
        raise StableOpsError(
            message="Max retries exceeded",
            status=0,
            code="max_retries_exceeded",
            details=None,
        )

    def _parse_error(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse error response."""
        try:
            return response.json()  # type: ignore[no-any-return]
        except Exception:
            return {"message": response.text or "Unknown error", "code": "unknown_error"}

    def _parse_retry_after(self, response: httpx.Response) -> Optional[float]:
        """Parse Retry-After header."""
        retry_after = response.headers.get("retry-after")
        if not retry_after:
            return None

        try:
            return float(retry_after)
        except ValueError:
            return None

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self) -> "HttpClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()


class AsyncHttpClient:
    """Asynchronous HTTP client with retry logic."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
        debug: DebugOption = None,
    ) -> None:
        """Initialize async HTTP client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._debug = _resolve_debug(debug)

        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": f"StableOpsSDK/{_SDK_VERSION}",
        }
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
        )

        if self._debug:
            self._debug(
                {
                    "type": "init",
                    "config": {
                        "base_url": self.base_url,
                        "api_key": mask_secret(api_key),
                        "timeout": self.timeout,
                        "max_retries": self.max_retries,
                        "base_delay": self.base_delay,
                        "max_delay": self.max_delay,
                    },
                }
            )

    async def request(
        self,
        method: HttpMethod,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        """Make async HTTP request with retry logic."""
        import asyncio

        url = path
        if query:
            filtered_query = {k: v for k, v in query.items() if v is not None}
            if filtered_query:
                url = f"{path}?{urlencode(filtered_query)}"

        headers = {}
        if idempotency_key:
            headers[IDEMPOTENCY_HEADER] = idempotency_key

        for attempt in range(self.max_retries + 1):
            started = time.monotonic()
            if self._debug:
                merged = {**dict(self.client.headers), **headers}
                self._debug(
                    {
                        "type": "request",
                        "method": method,
                        "url": f"{self.base_url}{url}",
                        "headers": _mask_headers(merged),
                        "body": body,
                        "attempt": attempt,
                    }
                )
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=body,
                    headers=headers,
                )
                if self._debug:
                    self._debug(
                        {
                            "type": "response",
                            "method": method,
                            "url": f"{self.base_url}{url}",
                            "status": response.status_code,
                            "duration_ms": int((time.monotonic() - started) * 1000),
                            "headers": dict(response.headers),
                            "body": _safe_json(response),
                            "attempt": attempt,
                        }
                    )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                status = e.response.status_code

                if 400 <= status < 500 and status != 429:
                    error_data = self._parse_error(e.response)
                    raise StableOpsError(
                        message=error_data.get("message", str(e)),
                        status=status,
                        code=error_data.get("code", "api_error"),
                        details=error_data.get("details"),
                    ) from e

                if attempt < self.max_retries and is_retryable_status(status):
                    retry_after = self._parse_retry_after(e.response)
                    delay = compute_delay(attempt, self.base_delay, self.max_delay, retry_after)
                    await asyncio.sleep(delay)
                    continue

                error_data = self._parse_error(e.response)
                raise StableOpsError(
                    message=error_data.get("message", str(e)),
                    status=status,
                    code=error_data.get("code", "api_error"),
                    details=error_data.get("details"),
                ) from e

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if self._debug:
                    self._debug(
                        {
                            "type": "error",
                            "method": method,
                            "url": f"{self.base_url}{url}",
                            "attempt": attempt,
                            "duration_ms": int((time.monotonic() - started) * 1000),
                            "error": {"type": type(e).__name__, "message": str(e)},
                        }
                    )
                if attempt < self.max_retries:
                    delay = compute_delay(attempt, self.base_delay, self.max_delay)
                    await asyncio.sleep(delay)
                    continue

                error_type = "timeout" if isinstance(e, httpx.TimeoutException) else "network_error"
                raise StableOpsError(
                    message=str(e),
                    status=0,
                    code=error_type,
                    details=None,
                ) from e

        raise StableOpsError(
            message="Max retries exceeded",
            status=0,
            code="max_retries_exceeded",
            details=None,
        )

    def _parse_error(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse error response."""
        try:
            return response.json()  # type: ignore[no-any-return]
        except Exception:
            return {"message": response.text or "Unknown error", "code": "unknown_error"}

    def _parse_retry_after(self, response: httpx.Response) -> Optional[float]:
        """Parse Retry-After header."""
        retry_after = response.headers.get("retry-after")
        if not retry_after:
            return None

        try:
            return float(retry_after)
        except ValueError:
            return None

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return response.text
