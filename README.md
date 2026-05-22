# python-openei

[![PyPI version](https://img.shields.io/pypi/v/python-openei.svg)](https://pypi.org/project/python-openei/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An asynchronous Python library for consuming utility rate data from the [OpenEI.org](https://openei.org) API and outputting it into an easy-to-use format.

## Features

- **Asynchronous API**: Fully built on `aiohttp` for non-blocking network calls.
- **Auto Caching**: Automatically caches API responses locally (24-hour expiration) to stay within rate limits.
- **Utility Plan Lookup**: Find utility rate plans by coordinates (latitude/longitude) or street address.
- **Rate Schedule Queries**: Calculates current and upcoming energy rates, demand rates, adjustments, and tier/sell rates for any given date and time.

---

## Installation

Install using `pip`:

```bash
pip install python-openei
```

---

## Quick Start

You will need an API key from [OpenEI.org](https://openei.org/wiki/Special:Register).

### Basic Usage

Here is a quick example of how to retrieve and query energy rates for a specific plan:

```python
import asyncio
from openeihttp import Rates

async def main():
    # Initialize Rates helper
    # Retrieve a specific plan (e.g. "539fca56ec12157c50403bf6")
    api = Rates(
        api="YOUR_OPENEI_API_KEY",
        plan="539fca56ec12157c50403bf6",
        cache_file="my_rate_cache.json"  # Optional local cache file
    )

    # Fetch/update the rate plan details
    await api.update()

    print(f"Rate Plan Name: {api.rate_name}")
    print(f"Current Energy Rate: ${api.current_rate}/kWh")
    print(f"Current Sell Rate: ${api.current_sell_rate}/kWh")

    # Check what the next rate will be and when it changes
    next_time = api.next_energy_rate_structure_time
    next_rate = api.next_energy_rate_structure
    print(f"Next rate change at: {next_time} (structure ID: {next_rate})")

asyncio.run(main())
```

---

## Plan Lookup

If you do not know the plan ID, you can look up available plans using a latitude/longitude pair or a physical address:

```python
import asyncio
from openeihttp import Rates

async def lookup():
    # Set up lookup using latitude and longitude
    api = Rates(
        api="YOUR_OPENEI_API_KEY",
        lat=37.7749,
        lon=-122.4194,
        radius=5.0  # Optional search radius in miles
    )

    plans = await api.lookup_plans()

    # plans will be grouped by utility name
    for utility, plan_list in plans.items():
        print(f"\nUtility: {utility}")
        for plan in plan_list:
            print(f"  - {plan['name']} (Plan Label: {plan['label']})")

asyncio.run(lookup())
```

---

## API Reference

### Properties

The `Rates` object exposes the following properties after a successful `update()`:

| Property | Return Type | Description |
| :--- | :--- | :--- |
| `rate_name` | `str` | Name of the utility rate plan. |
| `approval` | `bool` | Approval status of the rate plan on OpenEI. |
| `current_rate` | `float \| None` | Current active energy rate in $/kWh. |
| `current_sell_rate` | `float \| None` | Current net-metering / sell rate in $/kWh. |
| `current_adjustment` | `float \| None` | Current rate adjustment value in $/kWh. |
| `next_energy_rate_structure` | `int \| None` | Upcoming energy rate structure ID. |
| `next_energy_rate_structure_time` | `datetime \| None` | The time at which the next energy rate structure starts. |
| `current_demand_rate` | `float \| None` | Current demand rate. |
| `current_demand_adjustment`| `float \| None` | Current demand rate adjustment. |
| `demand_unit` | `str \| None` | The unit of the demand rate. |
| `monthly_tier_rate` | `float \| None` | Current tier rate based on monthly meter reading. |
| `distributed_generation` | `str \| None` | Distributed generation rules / net-metering type. |
| `mincharge` | `tuple[float, str] \| None` | Minimum charge amount and units (e.g. `(10.0, "$/month")`). |
| `fixedchargefirstmeter` | `tuple[float, str] \| None` | Fixed charge amount and units for the first meter. |

### Methods

- `await api.update()`: Updates the internal data. Loads from cache if fresh, otherwise fetches from API and caches locally.
- `await api.update_data()`: Forces a fresh API call (bypassing cache) and rewrites the cache file.
- `await api.clear_cache()`: Deletes the cache file if one was configured.
- `api.rate(date: datetime)`: Look up the energy rate for a specific date and time.
- `api.sell_rate(date: datetime)`: Look up the sell/net-metering rate for a specific date and time.
- `api.demand_rate(date: datetime)`: Look up the demand rate for a specific date and time.

---

## Development

This project uses `tox` to run checks and tests across Python versions.

### Run Tests and Linters

Make sure you have `tox` installed, then run:

```bash
tox
```
