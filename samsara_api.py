"""Samsara API client for driver management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import os

import requests  # type: ignore[import]
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class SamsaraAPI:
    """Simple wrapper around the Samsara Fleet API."""

    def __init__(self, api_key: str, base_url: str = "https://api.samsara.com"):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"

        max_attempts = int(os.getenv("SAMSARA_RETRY_ATTEMPTS", "5"))
        max_wait = int(os.getenv("SAMSARA_RETRY_MAX_WAIT", "32"))

        @retry(
            reraise=True,
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, max=max_wait),
            retry=retry_if_exception_type(requests.RequestException),
        )
        def send() -> requests.Response:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                params=params,
                json=json,
                timeout=30,
            )
            if response.status_code >= 500 or response.status_code == 429:
                raise requests.HTTPError(
                    f"HTTP {response.status_code}", response=response
                )
            return response

        response = send()
        response.raise_for_status()
        if response.content:
            return response.json()
        return None

    # Driver helpers -----------------------------------------------------

    def create_driver(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new driver."""
        return self._request("POST", "/fleet/drivers", json=data)

    def update_driver(self, driver_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing driver."""
        path = f"/fleet/drivers/{driver_id}"
        return self._request("PATCH", path, json=data)

    def update_driver_location(
        self, driver_id: str, location_tag_id: str
    ) -> Dict[str, Any]:
        """Update driver location tag."""
        payload = {"tagIds": [location_tag_id]}
        return self.update_driver(driver_id, payload)

    def find_driver_by_external_id(
        self, key: str, value: str
    ) -> Optional[Dict[str, Any]]:
        """Return the first driver matching an external ID."""
        params = {"externalIds": f"{key}:{value}"}
        result = self._request("GET", "/fleet/drivers", params=params) or {}
        drivers: List[Dict[str, Any]] = (
            result.get("drivers") or result.get("data") or []
        )
        return drivers[0] if drivers else None

    def deactivate_driver(self, driver_id: str, reason: str) -> Dict[str, Any]:
        """Deactivate a driver with a reason."""
        payload = {
            "driverActivationStatus": "deactivated",
            "deactivationReason": reason,
        }
        return self.update_driver(driver_id, payload)

    def list_drivers(self) -> List[Dict[str, Any]]:
        """Return all drivers."""
        result = self._request("GET", "/fleet/drivers") or {}
        return result.get("drivers") or result.get("data") or []
