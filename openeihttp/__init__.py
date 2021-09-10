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
        lat: float = None,
        lon: float = None,
        plan: str = None,
        radius: float = None,
        address: str = None,
        reading: float = None,
    ) -> None:
        """Initialize."""
        self._api = api
        self._lat = lat
        self._lon = lon
        self._plan = plan
        self._radius = radius
        self._reading = reading
        self._address = address
        self._data = None

    def lookup_plans(self) -> Dict[str, Any]:
        """Return the rate plan names per utility in the area."""
        url = f"{BASE_URL}version=latest&format=json"
        url = f"{url}&api_key={self._api}"
        url = f"{url}&sector=Residential"
        if self._radius is not None:
            url = f"{url}&radius={self._radius}"

        if self._address is None:
            url = f"{url}&lat={self._lat}&lon={self._lon}"
        else:
            url = f"{url}&address={self._address}"

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
        url = f"{BASE_URL}version=latest&format=json&sector=Residential"
        url = f"{url}&detail=full&api_key={self._api}"
        url = f"{url}&getpage={self._plan}"
        if self._radius is not None:
            url = f"{url}&radius={self._radius}"

        if self._address is None:
            url = f"{url}&lat={self._lat}&lon={self._lon}"
        else:
            url = f"{url}&address={self._address}"

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
    def current_rate(self) -> float | None:
        """Return the current rate."""
        assert self._data is not None
        if "energyratestructure" in self._data.keys():
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
            if self._reading:
                value = float(self._reading)
                rate_data = self._data["energyratestructure"][rate_structure]
                for rate in rate_data:
                    if "max" in rate.keys() and value < rate["max"]:
                        return rate["rate"]
                    continue
                return rate_data[-1]["rate"]
            rate = self._data["energyratestructure"][rate_structure][0]["rate"]
            return rate
        return None

    @property
    def monthly_tier_rate(self) -> float | None:
        """Return tier rate.

        Requires the monthy accumulative meter reading.
        """
        assert self._data is not None
        if "energyratestructure" in self._data.keys():
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
            if self._reading:
                value = float(self._reading)
                rate_data = self._data["energyratestructure"][rate_structure]
                for rate in rate_data:
                    if "max" in rate.keys() and value < (rate["max"] * 29):
                        return rate["rate"]
                    continue
                return rate_data[-1]["rate"]
            return None
        return None

    @property
    def all_rates(self) -> list | None:
        """Return the current rate."""
        assert self._data is not None
        if "energyratestructure" in self._data.keys():
            rates = []
            rate_data = self._data["energyratestructure"]
            for rate in rate_data:
                rates.append(rate[0]["rate"])

            return rates
        return None

    @property
    def current_demand_rate(self) -> float | None:
        """Return the current rate."""
        assert self._data is not None
        if "demandratestructure" in self._data.keys():
            weekend = False
            now = datetime.datetime.today()
            month = now.month - 1
            hour = now.hour
            if now.weekday() > 4:
                weekend = True
            table = "demandweekdayschedule"
            if weekend:
                table = "demandweekendschedule"

            lookup_table = self._data[table]
            rate_structure = lookup_table[month][hour]

            rate = self._data["demandratestructure"][rate_structure][0]["rate"]

            return rate
        return None

    @property
    def demand_unit(self) -> str | None:
        """Return the demand rate unit."""
        assert self._data is not None
        if "demandrateunit" in self._data.keys():
            return self._data["demandrateunit"]
        return None

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
    def distributed_generation(self) -> str | None:
        """Return the distributed generation name."""
        assert self._data is not None
        if "dgrules" in self._data.keys():
            return self._data["dgrules"]
        return None
