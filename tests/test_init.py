"""Test main functions."""

import datetime
import logging
import re

import aiohttp
import pytest
from aiohttp import RequestInfo
from aiohttp.client_exceptions import ContentTypeError
from freezegun import freeze_time
from yarl import URL

import openeihttp
from openeihttp import InvalidCall
from tests.common import load_fixture

pytestmark = pytest.mark.asyncio

TEST_URL = "https://api.openei.org/utility_rates"
TEST_REGEX = re.compile(r"^https://api\.openei\.org/utility_rates\?.*$")
DEFAULT_PLAN = "574613aa5457a3557e906f5b"

APS_PLANS = [
    {"name": "Time Advantage 7pm to noon", "label": "539fba68ec4f024bc1dc2db3"},
    {
        "name": "Residential Bundled & Adjustments No Tax TOU; Time Adv Super peak 7PM-Noon (ET-SP)",
        "label": "542aec8a5257a310694b1ab6",
    },
    {
        "name": "Residential Service Bundled Standard rate",
        "label": "55563ddf5457a3bf6c8b4570",
    },
    {
        "name": "Residential Bundled & Adjustments No Tax TOU ; Time Adv 7PM-Noon  (ET-2)",
        "label": "55563df55457a35e758b4568",
    },
    {
        "name": "Residential Bundled & Adjustments No Tax TOU w/ Demand; Combined Adv  7PM-Noon (ECT-2)",
        "label": "562bea025457a31838418740",
    },
    {
        "name": "Residential Service Bundled Standard rate",
        "label": "5743aa135457a3a636906f5b",
    },
    {
        "name": "Residential Service TOU Time Advantage 7PM-Noon (ET-2)",
        "label": "574613aa5457a3557e906f5b",
    },
    {
        "name": "Residential Service TOU Combined Advantage 7PM-Noon  (ECT-2)",
        "label": "574615f85457a3557e906f5c",
    },
    {
        "name": "Residential Service Standard (E-12)",
        "label": "5748ab725457a37e7d906f5b",
    },
    {
        "name": "Residential Service TOU Time Advantage 7PM-Noon (ET-2)",
        "label": "5748ac7a5457a37d7d906f5b",
    },
    {
        "name": "Residential Service Standard (E-12)",
        "label": "5881345e5457a35973316ce7",
    },
    {
        "name": "Residential Service TOU Time Advantage 7PM-Noon (ET-2)",
        "label": "588135ee5457a3873f316ce6",
    },
    {
        "name": "Residential Service TOU Combined Advantage 7PM-Noon  (ECT-2)",
        "label": "5890c92f5457a36c373dbec0",
    },
    {
        "name": "Residential Service Standard (E-12) Low Income",
        "label": "59fcde8e5457a3a04cc05084",
    },
    {
        "name": "Residential Service Standard (E-12) [Frozen]",
        "label": "5a592dee5457a3931d423a81",
    },
    {
        "name": "Residential Service TOU Time Advantage 7PM-Noon (ET-2) [Frozen]",
        "label": "5a5930055457a36274423a7d",
    },
    {
        "name": "Residential Service TOU Combined Advantage 7PM-Noon  (ECT-2) [Frozen]",
        "label": "5a5930bf5457a3371c423a7e",
    },
    {
        "name": "Residential Time of Use (Saver Choice)",
        "label": "5a5933d25457a3ad69423a81",
    },
    {
        "name": "Residential Service (Saver Choice Plus)",
        "label": "5a5935475457a3ad69423a82",
    },
    {
        "name": "Residential Service (Saver Choice Max)",
        "label": "5a5936ef5457a36274423a7f",
    },
    {
        "name": "Extra Small Residential Service (Lite Choice)",
        "label": "5a5937bb5457a3b71c423a7f",
    },
    {
        "name": "Small Residential Service (Premier Choice)",
        "label": "5a59388c5457a3931d423a84",
    },
    {
        "name": "Large Residential Service (Premier Choice Large)",
        "label": "5a5939515457a3371c423a7f",
    },
    {
        "name": "Residential Service (Pilot Technology Rate)",
        "label": "5a593d815457a3371c423a80",
    },
    {
        "name": "Extra Small Residential Service (Lite Choice) R-XS",
        "label": "5cacc5605457a379257780e2",
    },
    {
        "name": "Small Residential Service (Premier Choice) R-Basic",
        "label": "5cacc6545457a3634c7780e2",
    },
    {
        "name": "Large Residential Service (Premier Choice Large) R-Basic L [Frozen]",
        "label": "5cacc6e75457a3a8497780e2",
    },
    {
        "name": "Residential Time of Use (Saver Choice) TOU-E",
        "label": "5cacc7715457a393487780e2",
    },
    {
        "name": "Residential Service (Saver Choice Max)",
        "label": "5cacc9ae5457a3c6517780e2",
    },
    {
        "name": "Residential Service (Saver Choice Plus) R-2",
        "label": "5cacc9d15457a31d537780e2",
    },
    {
        "name": "Residential Service (Saver Choice Max) R-3",
        "label": "5caccb2f5457a3c8517780e2",
    },
    {
        "name": "Residential Service (Pilot Technology Rate) R-Tech",
        "label": "5caccd925457a31a537780e2",
    },
]

EXPECTED_LOOKUP_PLANS = {
    "Arizona Public Service Co": APS_PLANS,
    "Not Listed": [{"label": "Not Listed", "name": "Not Listed"}],
}


async def _load_rates(
    mock_aioclient, fixture: str, repeat: bool = False, **kwargs
) -> openeihttp.Rates:
    """Mock a plan fixture response, clear cache, and update a Rates instance."""
    mock_aioclient.get(
        TEST_REGEX,
        status=200,
        body=load_fixture(fixture),
        repeat=repeat,
    )
    defaults = {"api": "fakeAPIKey", "lat": "1", "lon": "1", "plan": DEFAULT_PLAN}
    defaults.update(kwargs)
    rates = openeihttp.Rates(**defaults)
    await rates.clear_cache()
    await rates.update()
    return rates


@pytest.mark.parametrize(
    "rates_kwargs",
    [
        {"api": "fakeAPIKey", "lat": "1", "lon": "1"},
        {"api": "fakeAPIKey", "address": "12345"},
    ],
    ids=["lat_lon", "address"],
)
async def test_get_lookup_data(rates_kwargs, mock_aioclient):
    """Test plan lookup by coordinates and by address."""
    mock_aioclient.get(TEST_REGEX, status=200, body=load_fixture("lookup.json"))
    rates = openeihttp.Rates(**rates_kwargs)
    assert await rates.lookup_plans() == EXPECTED_LOOKUP_PLANS


@freeze_time("2021-08-13 10:21:34")
async def test_get_rate_data(mock_aioclient, caplog):
    """Test rate schedules with custom cache file and logging."""
    assert datetime.datetime.now() == datetime.datetime(2021, 8, 13, 10, 21, 34)
    with caplog.at_level(logging.DEBUG):
        test_rates = await _load_rates(
            mock_aioclient,
            "plan_data.json",
            repeat=True,
            cache_file=f".cache/{DEFAULT_PLAN}",
        )
    assert test_rates.current_rate == 0.06118
    assert "No data populated, refreshing data." in caplog.text
    assert test_rates.current_sell_rate is None


@pytest.mark.parametrize(
    ("time_freeze", "expected_rate", "expected_adj"),
    [
        ("2021-08-13 13:20:00", 0.24477, 0.02824917),
        ("2021-08-14 13:20:00", 0.06118, 0.02138383),
    ],
    ids=["weekday_peak", "weekend"],
)
async def test_get_rate_data_schedules(time_freeze, expected_rate, expected_adj, mock_aioclient):
    """Test weekday and weekend energy rate schedules."""
    with freeze_time(time_freeze):
        test_rates = await _load_rates(mock_aioclient, "plan_data.json")
        assert test_rates.current_rate == expected_rate
        assert test_rates.current_adjustment == expected_adj


@pytest.mark.parametrize(
    ("time_freeze", "expected_rate", "expected_adj"),
    [
        ("2021-08-14 13:20:00", 0, None),
        ("2021-08-13 10:21:34", 0, None),
        ("2021-08-13 17:20:00", 8.4, 0.838),
    ],
    ids=["weekend", "weekday_offpeak", "weekday_peak"],
)
async def test_get_demand_rate_data(time_freeze, expected_rate, expected_adj, mock_aioclient):
    """Test demand rate schedules."""
    with freeze_time(time_freeze):
        test_rates = await _load_rates(mock_aioclient, "plan_demand_data.json")
        assert test_rates.current_demand_rate == expected_rate
        if expected_adj is not None:
            assert test_rates.current_demand_adjustment == expected_adj


@pytest.mark.parametrize(
    ("fixture", "attr", "expected"),
    [
        ("plan_demand_data.json", "demand_unit", "kW"),
        ("plan_data.json", "distributed_generation", "Net Metering"),
        ("plan_data.json", "approval", True),
        ("plan_data.json", "rate_name", "Residential Service TOU Time Advantage 7PM-Noon (ET-2)"),
        (
            "plan_data.json",
            "all_rates",
            (
                [0.24477, 0.06118, 0.19847, 0.06116],
                [0.02824917, 0.02138383, 0.02651779, 0.02138308],
            ),
        ),
        (
            "plan_demand_data.json",
            "all_rates",
            ([0.07798, 0.11017, 0.1316], [0.005741, 0.005741, 0.005741]),
        ),
        ("plan_tier_data.json", "mincharge", (10, "$/month")),
        ("plan_data.json", "mincharge", None),
        ("fixed_charge_rate.json", "fixedchargefirstmeter", (15.75, "$/month")),
        ("plan_tier_data.json", "fixedchargefirstmeter", None),
    ],
)
async def test_plan_properties(fixture, attr, expected, mock_aioclient):
    """Test plan metadata and charge properties."""
    test_rates = await _load_rates(mock_aioclient, fixture)
    assert getattr(test_rates, attr) == expected


@pytest.mark.parametrize(
    ("status_code", "expected_exc"),
    [
        (404, openeihttp.UrlNotFound),
        (401, openeihttp.NotAuthorized),
    ],
)
@pytest.mark.parametrize("call_type", ["lookup", "plan"])
async def test_http_errors(status_code, expected_exc, call_type, mock_aioclient):
    """Test HTTP 404 and 401 handling for lookup and plan updates."""
    mock_aioclient.get(TEST_REGEX, status=status_code, body="")
    if call_type == "lookup":
        rates = openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1")
        with pytest.raises(expected_exc):
            await rates.lookup_plans()
    else:
        rates = openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1", plan=DEFAULT_PLAN)
        await rates.clear_cache()
        with pytest.raises(expected_exc):
            await rates.update()


@pytest.mark.parametrize(
    ("fixture", "expected_exc", "expected_log", "call_type"),
    [
        (
            "api_error.json",
            openeihttp.APIError,
            "No api_key was supplied. Get one at https://api.openei.org:443",
            "plan",
        ),
        (
            "api_error.json",
            openeihttp.APIError,
            "No api_key was supplied. Get one at https://api.openei.org:443",
            "lookup",
        ),
        (
            "rate_limit.json",
            openeihttp.RateLimit,
            "You have exceeded your rate limit. Try again later or contact us at https://api.openei.org:443/contact/ for assistance",
            "plan",
        ),
    ],
)
async def test_api_errors(fixture, expected_exc, expected_log, call_type, mock_aioclient, caplog):
    """Test API error and rate limit responses."""
    mock_aioclient.get(TEST_REGEX, status=200, body=load_fixture(fixture))
    if call_type == "lookup":
        rates = openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1")
        with pytest.raises(expected_exc):
            await rates.lookup_plans()
    else:
        rates = openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1", plan=DEFAULT_PLAN)
        await rates.clear_cache()
        with pytest.raises(expected_exc):
            await rates.update()
    assert expected_log in caplog.text


async def test_get_lookup_data_radius(test_lookup_radius, mock_aioclient):
    """Test plan lookup with search radius."""
    mock_aioclient.get(TEST_REGEX, status=200, body=load_fixture("lookup_radius.json"))
    status = await test_lookup_radius.lookup_plans()
    assert status == {
        "Arizona Public Service Co": APS_PLANS,
        "Buckeye Water C&D District": [
            {"label": "539fb6fcec4f024bc1dc0679", "name": "Residential"},
            {"label": "539fc06bec4f024c27d89c25", "name": "Private Irrigation Pump"},
        ],
        "Salt River Project": [
            {
                "label": "539f755cec4f024411ed1357",
                "name": "E-23 STANDARD PRICE PLAN FOR RESIDENTIAL SERVICE",
            },
            {
                "label": "539fb6a4ec4f024bc1dc028f",
                "name": "E-24 M-POWER PRICE PLAN FOR PRE-PAY RESIDENTIAL SERVICE",
            },
            {
                "label": "539fb86aec4f024bc1dc1713",
                "name": "E-21 PRICE PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "539fbec8ec4f024c27d88a91",
                "name": "E-25 - Experimental Plan for Residential Super Peak Time-of-Use Service",
            },
            {
                "label": "539fc8d1ec4f024d2f53eab0",
                "name": "E-22 - EXPERIMENTAL PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "539fc9d6ec4f024d2f53f55c",
                "name": "E-28 M-POWER PRICE PLAN FOR RESIDENTIAL PRE-PAY TIME-OF-USE SERVICE",
            },
            {
                "label": "539fca4dec4f024d2f53fa1e",
                "name": "E-26 STANDARD PRICE PLAN FOR RESIDENTIAL TIME-OF-USE SERVICE",
            },
            {
                "label": "548a03535357a3ff32f0c30b",
                "name": "E-22 - EXPERIMENTAL PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "56c77d785457a3410cb338bb",
                "name": "E-23 BASIC PRICE PLAN FOR RESIDENTIAL SERVICE",
            },
            {
                "label": "56c77e775457a3fe28b338bb",
                "name": "E-26 STANDARD PRICE PLAN FOR RESIDENTIAL TIME-OF-USE SERVICE",
            },
            {
                "label": "56c780355457a30a29b338bb",
                "name": "E-24 M-POWER PRICE PLAN FOR PRE-PAY RESIDENTIAL SERVICE",
            },
            {
                "label": "56c781055457a3672db338bb",
                "name": "E-21 PRICE PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "56c781af5457a35833b338bc",
                "name": "E-22 - EXPERIMENTAL PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "56c7827e5457a3143ab338bb",
                "name": "E-25 - Experimental Plan for Residential Super Peak Time-of-Use Service",
            },
            {
                "label": "56c783fe5457a35833b338bd",
                "name": "E-28 M-POWER PRICE PLAN FOR RESIDENTIAL PRE-PAY TIME-OF-USE SERVICE",
            },
            {
                "label": "5880efe95457a35b73316ce6",
                "name": "E-23 BASIC PRICE PLAN FOR RESIDENTIAL SERVICE",
            },
            {
                "label": "5880f0db5457a3c97b316ce6",
                "name": "E-24 M-POWER PRICE PLAN FOR PRE-PAY RESIDENTIAL SERVICE",
            },
            {
                "label": "5880f1885457a3e863316ce6",
                "name": "E-26 STANDARD PRICE PLAN FOR RESIDENTIAL TIME-OF-USE SERVICE",
            },
            {
                "label": "5880f24d5457a33d48316ce6",
                "name": "E-21 PRICE PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "5880ff0c5457a3d70e316ce6",
                "name": "E-22 - EXPERIMENTAL PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "5881012e5457a30f3e316ce6",
                "name": "E-25 - Experimental Plan for Residential Super Peak Time-of-Use Service",
            },
            {
                "label": "588103e85457a3d70e316ce7",
                "name": "E-27 P Pilot Price Plan for Residential Demand Rate Service",
            },
            {
                "label": "5881042b5457a35b73316ce7",
                "name": "E-28 M-POWER PRICE PLAN FOR RESIDENTIAL PRE-PAY TIME-OF-USE SERVICE",
            },
            {
                "label": "59f8cac65457a32644c05083",
                "name": "E-23 BASIC PRICE PLAN FOR RESIDENTIAL SERVICE Low Income Rate",
            },
            {
                "label": "5a55224a5457a3ac5d423a7d",
                "name": "E-23 BASIC PRICE PLAN FOR RESIDENTIAL SERVICE",
            },
            {
                "label": "5a58f7fa5457a3ff19423a7c",
                "name": "E-21 PRICE PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "5a58f8ec5457a3931d423a7c",
                "name": "E-22 - EXPERIMENTAL PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "5a58f9605457a30e35423a7c",
                "name": "E-24 M-POWER PRICE PLAN FOR PRE-PAY RESIDENTIAL SERVICE",
            },
            {
                "label": "5a58f9cd5457a34151423a7c",
                "name": "E-25 - Experimental Plan for Residential Super Peak Time-of-Use Service",
            },
            {
                "label": "5a58fa865457a3ec1b423a7c",
                "name": "E-26 STANDARD PRICE PLAN FOR RESIDENTIAL TIME-OF-USE SERVICE",
            },
            {
                "label": "5a58fb8e5457a3b71c423a7c",
                "name": "E-27 P Pilot Price Plan for Residential Demand Rate Service",
            },
            {
                "label": "5a58fc915457a3ff19423a7d",
                "name": "E-28 M-POWER PRICE PLAN FOR RESIDENTIAL PRE-PAY TIME-OF-USE SERVICE",
            },
            {
                "label": "5a59008c5457a3ad69423a7c",
                "name": "E-29 EXPERIMENTAL PRICE PLAN FOR TIME-OF-USE "
                "SERVICE WITH SUPER OFF PEAK FOR ELECTRIC "
                "VEHICLES",
            },
            {
                "label": "5cf58ee05457a3160d26c07e",
                "name": "E-23 BASIC PRICE PLAN FOR RESIDENTIAL SERVICE",
            },
            {
                "label": "5cf815b25457a3be3326c07d",
                "name": "E-21 PRICE PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "5cf816af5457a35b2e26c07e",
                "name": "E-22 - EXPERIMENTAL PLAN FOR RESIDENTIAL SUPER PEAK TIME-OF-USE SERVICE",
            },
            {
                "label": "5cf8174b5457a3562a26c07d",
                "name": "E-24 M-POWER PRICE PLAN FOR PRE-PAY RESIDENTIAL SERVICE",
            },
            {
                "label": "5cf817db5457a32f3126c07d",
                "name": "E-25 - Experimental Plan for Residential Super Peak Time-of-Use Service",
            },
            {
                "label": "5cf8264e5457a3063126c07d",
                "name": "E-26 STANDARD PRICE PLAN FOR RESIDENTIAL TIME-OF-USE SERVICE",
            },
            {
                "label": "5cf826d55457a3063126c07e",
                "name": "E-27 P Pilot Price Plan for Residential Demand Rate Service",
            },
            {
                "label": "5cf82a395457a3d92b26c07d",
                "name": "E-29 EXPERIMENTAL PRICE PLAN FOR TIME-OF-USE "
                "SERVICE WITH SUPER OFF PEAK FOR ELECTRIC "
                "VEHICLES",
            },
            {
                "label": "5cf831715457a3612f26c07d",
                "name": "E-28 M-POWER PRICE PLAN FOR RESIDENTIAL PRE-PAY TIME-OF-USE SERVICE",
            },
            {
                "label": "5d9b7fc95457a3d865598dce",
                "name": "E-14 RESIDENTIAL CUSTOMER GENERATION ELECTRIC VEHICLE EXPORT PRICE PLAN",
            },
            {
                "label": "5dc498485457a37b0cf6a951",
                "name": "E-13 CUSTOMER GENERATION TIME-OF-USE EXPORT "
                "PRICE PLAN FOR RESIDENTIAL SERVICE",
            },
            {
                "label": "5dc49b5f5457a39661f6a951",
                "name": "E-15 CUSTOMER GENERATION AVERAGE DEMAND "
                "PRICE PLAN FOR RESIDENTIAL SERVICE",
            },
        ],
        "Not Listed": [{"label": "Not Listed", "name": "Not Listed"}],
    }


@pytest.mark.parametrize(
    ("reading", "time_freeze", "expected_rate", "expected_structure"),
    [
        ("5.1", "2021-08-13 10:21:34", 0.25902, 0),
        ("5.1", "2021-11-01 10:21:34", 0.25902, 1),
        ("10.3", "2021-08-13 10:21:34", 0.32596, 0),
        ("40.1", "2021-08-13 10:21:34", 0.40745, 0),
        ("5.1", "2021-08-13 13:20:00", 0.25902, 0),
        ("5.1", "2021-08-14 13:20:00", 0.25902, 0),
    ],
)
async def test_get_tier_rate_data(
    reading, time_freeze, expected_rate, expected_structure, mock_aioclient
):
    """Test rate schedules for different tiers."""
    with freeze_time(time_freeze):
        test_rates = await _load_rates(mock_aioclient, "plan_tier_data.json", reading=reading)
        assert test_rates.current_rate == expected_rate
        assert test_rates.current_energy_rate_structure == expected_structure


@pytest.mark.parametrize(
    ("time_freeze", "fixture", "expected_current", "expected_next", "expected_time"),
    [
        ("2025-01-01 10:21:34", "plan_data.json", 3, 2, datetime.datetime(2025, 1, 1, 12, 0)),
        ("2025-01-01 23:21:34", "plan_data.json", 3, 2, datetime.datetime(2025, 1, 2, 12, 0)),
        ("2025-01-03 23:21:34", "plan_data.json", 3, 2, datetime.datetime(2025, 1, 6, 12, 0)),
        ("2025-01-03 23:21:34", "plan_tier_data.json", 1, 0, datetime.datetime(2025, 5, 1, 0, 0)),
        ("2025-01-04 23:21:34", "plan_tier_data.json", 1, 0, datetime.datetime(2025, 5, 1, 0, 0)),
        ("2024-11-01 23:21:34", "plan_tier_data.json", 1, 0, datetime.datetime(2025, 5, 1, 0, 0)),
    ],
    ids=[
        "same_day",
        "next_day",
        "weekend_loop",
        "next_month",
        "next_month_weekend_start",
        "next_year",
    ],
)
async def test_get_next_rate_structure(
    time_freeze, fixture, expected_current, expected_next, expected_time, mock_aioclient
):
    """Test calculating the next rate structure across day, weekend, month, and year transitions."""
    with freeze_time(time_freeze):
        test_rates = await _load_rates(mock_aioclient, fixture)
        assert test_rates.current_energy_rate_structure == expected_current
        assert test_rates.next_energy_rate_structure == expected_next
        assert test_rates.next_energy_rate_structure_time == expected_time


@pytest.mark.parametrize(
    ("reading", "expected_rate"),
    [
        ("114", 0.25902),
        ("301", 0.32596),
        ("1300", 0.40745),
    ],
)
@freeze_time("2021-08-13 10:21:34")
async def test_get_monthly_tier_rate_data(reading, expected_rate, mock_aioclient):
    """Test monthly tier rate schedules."""
    test_rates = await _load_rates(mock_aioclient, "plan_tier_data.json", reading=reading)
    assert test_rates.monthly_tier_rate == expected_rate


@freeze_time("2021-08-13 10:21:34")
async def test_get_rate_data_address(test_rates_address, mock_aioclient):
    """Test rate schedules using address."""
    mock_aioclient.get(TEST_REGEX, status=200, body=load_fixture("plan_data.json"))
    await test_rates_address.clear_cache()
    await test_rates_address.update()
    assert test_rates_address.current_rate == 0.06118


async def test_missing_loc(test_lookup_missing_loc, caplog):
    """Test missing location raises InvalidCall."""
    with pytest.raises(InvalidCall):
        await test_lookup_missing_loc.lookup_plans()
    assert "Missing location data for a plan lookup." in caplog.text


async def test_get_rate_data_cache(mock_aioclient, caplog):
    """Test cache population and stale refresh."""
    mock_aioclient.get(TEST_REGEX, status=200, body=load_fixture("plan_data.json"), repeat=True)
    test_rates = openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1", plan=DEFAULT_PLAN)
    with caplog.at_level(logging.DEBUG):
        await test_rates.update()
    assert "No data populated, refreshing data." in caplog.text
    thefuture = datetime.date.today() + datetime.timedelta(days=3)
    with freeze_time(thefuture), caplog.at_level(logging.DEBUG):
        await test_rates.update()
    assert "Data stale, refreshing from API." in caplog.text


@pytest.mark.parametrize(
    ("time_freeze", "expected_rate"),
    [
        ("2021-08-13 14:20:00", 0.150563),
        ("2021-08-13 09:20:00", 0.099222),
        ("2021-11-13 09:20:00", 0.085252),
    ],
)
async def test_get_sell_rate_data(time_freeze, expected_rate, mock_aioclient):
    """Test sell rate schedules."""
    with freeze_time(time_freeze):
        test_rates = await _load_rates(mock_aioclient, "sell_rate.json")
        assert test_rates.current_sell_rate == expected_rate


@pytest.mark.parametrize("call_type", ["lookup", "plan"])
@pytest.mark.parametrize(
    ("mock_kwargs", "expected_log"),
    [
        ({"exception": TimeoutError("Timeout")}, "Timeout while updating"),
        ({"status": 200, "body": "Not a JSON string"}, "Error: Not a JSON string"),
    ],
    ids=["timeout", "non_json"],
)
async def test_request_failures(call_type, mock_kwargs, expected_log, mock_aioclient, caplog):
    """Test timeout and non-JSON responses for lookup and plan updates."""
    mock_aioclient.get(TEST_REGEX, **mock_kwargs)
    if call_type == "lookup":
        rates = openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1")
        with pytest.raises(openeihttp.APIError):
            await rates.lookup_plans()
    else:
        rates = openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1", plan=DEFAULT_PLAN)
        await rates.clear_cache()
        with pytest.raises(openeihttp.APIError):
            await rates.update()
    assert expected_log in caplog.text


async def test_get_lookup_data_content_type_error(mock_aioclient, caplog):
    """Test lookup_plans handles ContentTypeError gracefully."""
    req_info = RequestInfo(url=URL(TEST_URL), method="GET", headers=None)
    mock_aioclient.get(
        TEST_REGEX,
        exception=ContentTypeError(
            req_info,
            (),
            message="Attempt to decode JSON with unexpected mimetype",
        ),
    )
    test_lookup = openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1")
    with pytest.raises(openeihttp.APIError):
        await test_lookup.lookup_plans()
    assert "Attempt to decode JSON with unexpected mimetype" in caplog.text


async def test_session_reuse(mock_aioclient):
    """Test custom session is used and not closed."""
    mock_aioclient.get(TEST_REGEX, status=200, body=load_fixture("lookup.json"))
    async with aiohttp.ClientSession() as custom_session:
        test_lookup = openeihttp.Rates(
            api="fakeAPIKey",
            lat=1.0,
            lon=1.0,
            session=custom_session,
        )
        status = await test_lookup.lookup_plans()
        assert status is not None
        assert not custom_session.closed


async def test_default_none_coordinates():
    """Test that default coordinates are None."""
    test_lookup = openeihttp.Rates(api="fakeAPIKey")
    assert test_lookup._lat is None
    assert test_lookup._lon is None


@pytest.mark.parametrize("coord_kwargs", [{"lat": 1.0}, {"lon": 1.0}], ids=["lat_only", "lon_only"])
async def test_partial_coordinates(coord_kwargs):
    """Test that partial coordinates raise InvalidCall."""
    test_lookup = openeihttp.Rates(api="fakeAPIKey", **coord_kwargs)
    with pytest.raises(openeihttp.InvalidCall):
        await test_lookup.lookup_plans()


@freeze_time("2021-08-13 10:21:34")
async def test_missing_rate_structures_and_reading_adjustment(mock_aioclient):
    """Test None returns when rate structures or readings are missing, and tiered adjustment."""
    test_rates = await _load_rates(mock_aioclient, "plan_data.json")
    assert test_rates.monthly_tier_rate is None
    assert test_rates.current_demand_adjustment is None

    # Test tiered adjustment when reading is set and adj is present on last tier
    test_rates._reading = 10.0
    assert test_rates.current_adjustment == 0.02138383

    # Test missing energyratestructure
    test_rates._data = {}
    test_rates._reading = 0.0
    assert test_rates.current_rate is None
    assert test_rates.current_adjustment is None
