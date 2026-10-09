"""Thin HubSpot REST client: auth, pagination, rate limiting, and scope-aware degradation.

Every call is read-only. Nothing in this package writes to the portal.
"""

from __future__ import annotations

import os
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Iterator

import requests

BASE = "https://api.hubapi.com"

# HubSpot's standard private-app ceiling is 110 requests / 10s. Leave headroom so a
# concurrently running integration does not push the portal over the limit.
_RATE_LIMIT = 90
_RATE_WINDOW = 10.0


class ScopeError(RuntimeError):
    """The token lacks the scope, or the portal lacks the plan tier, for an endpoint.

    Carries the scope names HubSpot itself said were missing, when it names them, so
    the report can tell the reader exactly which boxes to tick rather than guessing.
    """

    def __init__(self, message: str, scopes: list[str] | None = None) -> None:
        super().__init__(message)
        self.scopes = scopes or []


class _RateLimiter:
    def __init__(self, limit: int = _RATE_LIMIT, window: float = _RATE_WINDOW) -> None:
        self._limit = limit
        self._window = window
        self._hits: list[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                self._hits = [t for t in self._hits if now - t < self._window]
                if len(self._hits) < self._limit:
                    self._hits.append(now)
                    return
                sleep_for = self._window - (now - self._hits[0])
            time.sleep(max(sleep_for, 0.01))


@dataclass
class Skipped:
    """Recorded when an endpoint is unreachable, so the report can say so explicitly."""

    endpoint: str
    status: int | None
    reason: str
    required_scopes: list[str] = field(default_factory=list)


@dataclass
class Client:
    token: str
    timeout: int = 30
    max_retries: int = 5
    skipped: list[Skipped] = field(default_factory=list)
    _limiter: _RateLimiter = field(default_factory=_RateLimiter)
    _session: requests.Session = field(default_factory=requests.Session)

    @classmethod
    def from_env(cls) -> "Client":
        token = os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()
        if not token:
            raise SystemExit(
                "HUBSPOT_ACCESS_TOKEN is not set. Copy .env.example to .env and add your "
                "HubSpot private app token, or export it in the shell."
            )
        return cls(token=token)

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Issue one request, retrying on 429 and 5xx. Raises ScopeError on 401/403."""
        url = path if path.startswith("http") else f"{BASE}{path}"
        last_exc: Exception | None = None

        for attempt in range(self.max_retries):
            self._limiter.acquire()
            try:
                resp = self._session.request(
                    method, url, headers=self._headers, timeout=self.timeout, **kwargs
                )
            except requests.RequestException as exc:  # network flake
                last_exc = exc
                time.sleep(2**attempt)
                continue

            if resp.status_code == 429:
                wait = float(resp.headers.get("Retry-After", 2**attempt))
                time.sleep(min(wait, 30))
                continue
            if resp.status_code in (401, 403):
                raise ScopeError(
                    f"{resp.status_code} on {path}: {resp.text[:300]}",
                    scopes=_required_scopes(resp),
                )
            if resp.status_code == 404:
                raise ScopeError(f"404 on {path} (endpoint not available for this portal)")
            if resp.status_code >= 500:
                time.sleep(2**attempt)
                continue

            resp.raise_for_status()
            if not resp.content:
                return {}
            return resp.json()

        raise RuntimeError(f"{method} {path} failed after {self.max_retries} attempts: {last_exc}")

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("GET", path, params=params or {})

    def post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", path, json=json_body)

    def paginate(
        self, path: str, params: dict[str, Any] | None = None, limit: int = 100
    ) -> Iterator[dict[str, Any]]:
        """Walk a v3/v4 cursor-paginated collection endpoint."""
        after: str | None = None
        while True:
            page_params = dict(params or {})
            page_params["limit"] = limit
            if after:
                page_params["after"] = after
            data = self.get(path, page_params)
            yield from data.get("results", [])
            after = (data.get("paging") or {}).get("next", {}).get("after")
            if not after:
                return

    def collect(self, label: str, path: str, params: dict[str, Any] | None = None,
                limit: int = 100) -> list[dict[str, Any]]:
        """Paginate an endpoint, recording a skip instead of failing when it is unavailable."""
        try:
            return list(self.paginate(path, params, limit))
        except ScopeError as exc:
            self.skipped.append(Skipped(
                endpoint=path, status=_status_of(exc), reason=str(exc),
                required_scopes=exc.scopes,
            ))
            print(f"  ! {label}: unavailable ({exc})")
            return []


def _required_scopes(resp: requests.Response) -> list[str]:
    """Pull the scope names out of a HubSpot 403 body.

    HubSpot returns them under errors[].context.requiredGranularScopes. Reading them
    is far more reliable than mapping endpoints to scopes by hand, because HubSpot
    renames and splits scopes over time.
    """
    try:
        payload = resp.json()
    except ValueError:
        return []
    found: list[str] = []
    for error in payload.get("errors", []) or []:
        for name in (error.get("context") or {}).get("requiredGranularScopes", []) or []:
            if name not in found:
                found.append(name)
    return found


def _status_of(exc: ScopeError) -> int | None:
    head = str(exc).split(" ", 1)[0]
    return int(head) if head.isdigit() else None
