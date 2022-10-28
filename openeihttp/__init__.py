"""Provide a package for python-openei."""
from __future__ import annotations

import datetime
import logging
import time
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


class RateLimit(Exception):
    """Exception for API errors."""


class InvalidCall(Exception):
    """Exception for invalid library calls."""


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
        self._redact = [
            self._api,
            self._address,
        ]
        self._timestamp = datetime.datetime(1990, 1, 1, 0, 0, 0)

    def lookup_plans(self) -> Dict[str, Any]:
        """Return the rate plan names per utility in the area."""
        if not any([self._address, self._lat, self._lon]):
            _LOGGER.error("Missing location data for a plan lookup.")
            raise InvalidCall

        thetime = time.time()

        url = f"{BASE_URL}version=latest&format=json"
        url = f"{url}&api_key={self._api}&orderby=startdate"
        url = f"{url}&sector=Residential&effective_on_date={thetime}"
        if self._radius is not None:
            url = f"{url}&radius={self._radius}"

        if self._address is None:
            url = f"{url}&lat={self._lat}&lon={self._lon}"
        else:
            url = f"{url}&address={self._address}"

        rate_names: Dict[str, Any] = {}
        msg = url
        for redact in self._redact:
            if redact:
                msg = msg.replace(str(redact), "[REDACTED]")
        redact_msg = "&lat=[REDACTED]&lon=[REDACTED]"
        msg = msg.replace(f"&lat={self._lat}&lon={self._lon}", redact_msg)
        _LOGGER.debug("Looking up plans via URL: %s", msg)

        result = requests.get(url, timeout=90)
        if result.status_code == 404:
            raise UrlNotFound
        if result.status_code == 401:
            raise NotAuthorized

        if "error" in result.json():
            message = result.json()["error"]["message"]
            _LOGGER.error("Error: %s", message)
            raise APIError

        if "items" in result.json():
            for item in result.json()["items"]:
                utility: str = item["utility"]
                if utility not in rate_names:
                    rate_names[utility] = []
                info = {"name": item["name"], "label": item["label"]}
                rate_names[utility].append(info)

        notlisted = "Not Listed"
        rate_names[notlisted] = [{"name": notlisted, "label": notlisted}]
        return rate_names

    def update(self) -> None:
        """Update data only if we need to."""
        if self._data is None:
            _LOGGER.debug("No data populated, refreshing data.")
            self.update_data()
            self._timestamp = datetime.datetime.now()
        else:
            elapsedtime = datetime.datetime.now() - self._timestamp
            past = datetime.timedelta(hours=24)
            if elapsedtime >= past:
                _LOGGER.debug("Data stale, refreshing from API.")
                self.update_data()
                self._timestamp = datetime.datetime.now()

    def update_data(self) -> None:
        """Update the data."""
        url = f"{BASE_URL}version=latest&format=json&detail=full"
        url = f"{url}&api_key={self._api}&getpage={self._plan}"

        msg = url
        for redact in self._redact:
            if redact:
                msg = msg.replace(str(redact), "[REDACTED]")
        _LOGGER.debug("Updating data via URL: %s", msg)

        result = requests.get(url, timeout=90)
        if result.status_code == 404:
            raise UrlNotFound
        if result.status_code == 401:
            raise NotAuthorized

        if "error" in result.json():
            message = result.json()["error"]["message"]
            _LOGGER.error("Error: %s", message)
            if "You have exceeded your rate limit." in message:
                raise RateLimit
            raise APIError

        if "items" in result.json():
            data = result.json()["items"][0]
            self._data = data
            _LOGGER.debug("Data updated, results: %s", self._data)

    @property
    def current_rate(self) -> float | None:
        """Return the current rate."""
        assert self._data is not None
        if "energyratestructure" in self._data:
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
                    if "max" in rate and value < rate["max"]:
                        return rate["rate"]
                    continue
                return rate_data[-1]["rate"]
            rate = self._data["energyratestructure"][rate_structure][0]["rate"]
            return rate
        return None

    @property
    def current_adjustment(self) -> float | None:
        """Return the current rate."""
        assert self._data is not None
        if "energyratestructure" in self._data:
            adj = None
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
                rate_data = self._data["energyratestructure"][rate_structure]
                if "adj" in rate_data[-1]:
                    return rate_data[-1]["adj"]
            adj_data = self._data["energyratestructure"][rate_structure][0]
            if "adj" in adj_data:
                adj = adj_data["adj"]
            return adj
        return None

    @property
    def monthly_tier_rate(self) -> float | None:
        """Return tier rate.

        Requires the monthy accumulative meter reading.
        """
        assert self._data is not None
        if "energyratestructure" in self._data:
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
                    if "max" in rate and value < (rate["max"] * 29):
                        return rate["rate"]
                    continue
                return rate_data[-1]["rate"]
            return None
        return None

    @property
    def all_rates(self) -> tuple | None:
        """Return the current rate."""
        assert self._data is not None
        if "energyratestructure" in self._data:
            rates = []
            adjs = []
            rate_data = self._data["energyratestructure"]
            for rate in rate_data:
                rates.append(rate[0]["rate"])
                adjs.append(rate[0]["adj"])

            return rates, adjs
        return None

    @property
    def current_demand_rate(self) -> float | None:
        """Return the current rate."""
        assert self._data is not None
        if "demandratestructure" in self._data:
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
    def current_demand_adjustment(self) -> float | None:
        """Return the current rate."""
        assert self._data is not None
        if "demandratestructure" in self._data:
            adj = None
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

            adj_data = self._data["demandratestructure"][rate_structure][0]
            if "adj" in adj_data:
                adj = adj_data["adj"]
            return adj
        return None

    @property
    def demand_unit(self) -> str | None:
        """Return the demand rate unit."""
        assert self._data is not None
        if "demandrateunit" in self._data:
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
        if "dgrules" in self._data:
            return self._data["dgrules"]
        return None

    @property
    def mincharge(self) -> tuple | None:
        """Return the mincharge."""
        assert self._data is not None
        if "mincharge" in self._data:
            return (self._data["mincharge"], self._data["minchargeunits"])
        return None
