"""Provide a package for python-openei."""
from __future__ import annotations

import datetime
import logging
from typing import Any, Dict
import requests  # type: ignore
from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)


class UrlNotFound(Exception):
    """Exception for NotFound."""


class NotAuthorized(Exception):
    """Exception for invalid API key."""


class APIError(Exception):
    """Exception for API errors."""


class Rates:
    """Represent OpenEI Rates."""

    def __init__(
        self,
        api: str,
        lat: float,
        lon: float,
        plan: str = None,
    ) -> None:
        """Initialize."""
        self._api = api
        self._lat = lat
        self._lon = lon
        self._plan = plan
        self._data = None

    def lookup_plans(self) -> Dict[str, Any]:
        """Return the rate plan names per utility in the area."""
        url = f"{BASE_URL}version=latest&format=json"
        url = f"{url}&api_key={self._api}&lat={self._lat}&lon={self._lon}"
        url = f"{url}&sector=Residential"
        rate_names: Dict[str, Any] = {}

        result = requests.get(url)
        if result.status_code == 404:
            raise UrlNotFound
        if result.status_code == 401:
            raise NotAuthorized

        if "error" in result.json().keys():
            message = result.json()["error"]["message"]
            _LOGGER.error("Error: %s", message)
            raise APIError

        if "items" in result.json().keys():
            for item in result.json()["items"]:
                utility: str = item["utility"]
                if utility not in rate_names.keys():
                    rate_names[utility] = []
                info = {"name": item["name"], "label": item["label"]}
                rate_names[utility].append(info)

        return rate_names

    def update(self) -> None:
        """Update the data."""
        url = f"{BASE_URL}version=latest&format=json"
        url = f"{url}&api_key={self._api}&lat={self._lat}&lon={self._lon}"
        url = f"{url}&sector=Residential&detail=full&getpage={self._plan}"

        result = requests.get(url)
        if result.status_code == 404:
            raise UrlNotFound
        if result.status_code == 401:
            raise NotAuthorized

        if "error" in result.json().keys():
            message = result.json()["error"]["message"]
            _LOGGER.error("Error: %s", message)
            raise APIError

        if "items" in result.json().keys():
            data = result.json()["items"][0]
            self._data = data

    @property
    def current_rate(self) -> float:
        """Return the current rate."""
        assert self._data is not None
        weekend = False
        now = datetime.datetime.today()
        month = now.month - 1
        hour = now.hour
        if now.weekday() > 4:
            weekend = True
        table = "energyweekdayschedule"
        if weekend:
            table = "energyweekendschedule"

        lookup_table = self._data[table]
        rate_structure = lookup_table[month][hour]

        rate = self._data["energyratestructure"][rate_structure][0]["rate"]

        return rate

    @property
    def rate_name(self) -> str:
        """Return the rate name."""
        assert self._data is not None
        return self._data["name"]

    @property
    def approval(self) -> bool:
        """Return the rate name."""
        assert self._data is not None
        return self._data["approved"]

    @property
    def distributed_generation(self) -> str:
        """Return the distributed generation name."""
        assert self._data is not None
        return self._data["dgrules"]
