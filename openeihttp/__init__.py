"""Provide a package for python-openei."""

from __future__ import annotations

import datetime
import json
import logging
import time
from typing import Any, Dict

import aiohttp  # type: ignore
from aiohttp.client_exceptions import ContentTypeError, ServerTimeoutError

from .cache import OpenEICache
from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
}
ERROR_TIMEOUT = "Timeout while updating"


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


# pylint: disable=too-many-positional-arguments
class Rates:
    """Represent OpenEI Rates."""

    def __init__(
        self,
        api: str,
        lat: float = 9000,
        lon: float = 9000,
        plan: str = "",
        radius: float = 0.0,
        address: str = "",
        reading: float = 0.0,
        cache_file: str = None,
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
        self._cache_file = cache_file
        self._timestamp = datetime.datetime(1990, 1, 1, 0, 0, 0)

    async def process_request(self, params: dict, timeout: int = 90) -> dict[str, Any]:
        """Process API requests."""
        async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as session:
            _LOGGER.debug("URL: %s", BASE_URL)
            try:
                async with session.get(
                    BASE_URL, params=params, timeout=timeout
                ) as response:
                    message: Any = {}
                    try:
                        message = await response.text()
                    except UnicodeDecodeError:
                        _LOGGER.debug("Decoding error.")
                        data = await response.read()
                        message = data.decode(errors="replace")

                    try:
                        message = json.loads(message)
                    except ValueError:
                        _LOGGER.warning("Non-JSON response: %s", message)
                        message = {"error": message}

                    if response.status == 404:
                        raise UrlNotFound
                    if response.status == 401:
                        raise NotAuthorized
                    if response.status != 200:
                        _LOGGER.error(  # pylint: disable-next=line-too-long
                            "An error reteiving data from the server, code: %s\nmessage: %s",  # noqa: E501
                            response.status,
                            message,
                        )
                        message = {"error": message}
                    return message

            except (TimeoutError, ServerTimeoutError):
                _LOGGER.error("%s: %s", ERROR_TIMEOUT, BASE_URL)
                message = {"error": ERROR_TIMEOUT}
            except ContentTypeError as err:
                _LOGGER.error("%s", err)
                message = {"error": err}

            await session.close()
            return message

    async def lookup_plans(self) -> Dict[str, Any]:
        """Return the rate plan names per utility in the area."""
        if self._address == "" and (self._lat == 9000 and self._lon == 9000):
            _LOGGER.error("Missing location data for a plan lookup.")
            raise InvalidCall

        thetime = time.time()

        params = {
            "version": "latest",
            "format": "json",
            "api_key": self._api,
            "orderby": "startdate",
            "sector": "Residential",
            "effective_on_date": thetime,
        }

        if self._radius != 0.0:
            params["radius"] = self._radius

        if self._address == "":
            params["lat"] = self._lat
            params["lon"] = self._lon
        else:
            params["address"] = self._address

        rate_names: Dict[str, Any] = {}

        result = await self.process_request(params, timeout=90)

        if "error" in result.keys():
            message = result["error"]["message"]
            _LOGGER.error("Error: %s", message)
            raise APIError

        if "items" in result.keys():
            for item in result["items"]:
                utility: str = item["utility"]
                if utility not in rate_names:
                    rate_names[utility] = []
                info = {"name": item["name"], "label": item["label"]}
                rate_names[utility].append(info)

        notlisted = "Not Listed"
        rate_names[notlisted] = [{"name": notlisted, "label": notlisted}]
        return rate_names

    async def update(self) -> None:
        """Update data only if we need to."""
        if self._data is None:
            _LOGGER.debug("No data populated, refreshing data.")
            if self._cache_file:
                cache = OpenEICache(self._cache_file)
            else:
                cache = OpenEICache()
            # Load cached file if one exists
            if await cache.cache_exists():
                _LOGGER.debug("Cache file exists, reading...")
                self._data = await cache.read_cache()
            else:
                _LOGGER.debug("Cache file missing, pulling API data...")
                await self.update_data()
            self._timestamp = datetime.datetime.now()
        else:
            elapsedtime = datetime.datetime.now() - self._timestamp
            past = datetime.timedelta(hours=24)
            if elapsedtime >= past:
                _LOGGER.debug("Data stale, refreshing from API.")
                await self.update_data()
                self._timestamp = datetime.datetime.now()

    async def update_data(self) -> None:
        """Update the data."""
        params = {
            "version": "latest",
            "format": "json",
            "detail": "full",
            "api_key": self._api,
            "getpage": self._plan,
        }

        result = await self.process_request(params, timeout=90)

        if "error" in result.keys():
            message = result["error"]["message"]
            _LOGGER.error("Error: %s", message)
            if "You have exceeded your rate limit." in message:
                raise RateLimit
            raise APIError

        if "items" in result.keys():
            data = result["items"][0]
            self._data = data
            # Insert cache writing call here
            if self._cache_file:
                cache = OpenEICache(self._cache_file)
            else:
                cache = OpenEICache()
            json_data = json.dumps(data).encode("utf-8")
            await cache.write_cache(json_data)
            _LOGGER.debug("Data updated, results: %s", self._data)

    async def clear_cache(self) -> None:
        """Clear cache file."""
        if self._cache_file:
            cache = OpenEICache(self._cache_file)
        else:
            cache = OpenEICache()
        await cache.clear_cache()

    @property
    def current_energy_rate_structure(self) -> int | None:
        """Return the current rate structure."""
        return self.rate_structure(datetime.datetime.today(), "energy")

    def rate_structure(self, date, rate_type) -> int | None:
        """Return the rate structure for a specific date."""
        assert self._data is not None
        if f"{rate_type}ratestructure" in self._data:
            month = date.month - 1
            hour = date.hour
            weekend = date.weekday() > 4

            table = (
                f"{rate_type}weekendschedule"
                if weekend
                else f"{rate_type}weekdayschedule"
            )
            lookup_table = self._data[table]
            rate_structure = lookup_table[month][hour]

            return rate_structure
        return None

    @property
    def current_rate(self) -> float | None:
        """Return the current rate."""
        return self.rate(datetime.datetime.today())

    def rate(self, date) -> float | None:
        """Return the rate for a specific date."""
        assert self._data is not None
        rate_structure = self.rate_structure(date, "energy")
        if rate_structure is not None:
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
        return self.adjustment(datetime.datetime.today())

    def adjustment(self, date) -> float | None:
        """Return the rate for a specific date."""
        assert self._data is not None
        rate_structure = self.rate_structure(date, "energy")
        if rate_structure is not None:
            adj = None
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
        return self.tier_rate_for_month(datetime.datetime.today())

    def tier_rate_for_month(self, date) -> float | None:
        """Return tier rate for a specific month.

        Requires the monthy accumulative meter reading.
        """
        assert self._data is not None
        rate_structure = self.rate_structure(date, "energy")
        if rate_structure is not None:
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
                if "adj" in rate[0]:
                    adjs.append(rate[0]["adj"])

            return rates, adjs
        return None

    @property
    def current_demand_rate(self) -> float | None:
        """Return the current rate."""
        return self.demand_rate(datetime.datetime.today())

    def demand_rate(self, date) -> float | None:
        """Return the rate for a specific date."""
        assert self._data is not None
        rate_structure = self.rate_structure(date, "demand")
        if rate_structure is not None:
            rate = self._data["demandratestructure"][rate_structure][0]["rate"]
            return rate
        return None

    @property
    def current_demand_adjustment(self) -> float | None:
        """Return the current rate."""
        return self.demand_adjustment(datetime.datetime.today())

    def demand_adjustment(self, date) -> float | None:
        """Return the rate for a specific date."""
        assert self._data is not None
        rate_structure = self.rate_structure(date, "demand")
        if rate_structure is not None:
            adj = None

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
