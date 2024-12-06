"""Provide common pytest fixtures."""

import pytest
from aioresponses import aioresponses

import openeihttp

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_aioclient():
    """Fixture to mock aioclient calls."""
    with aioresponses() as m:
        yield m


@pytest.fixture(name="test_lookup")
def test_lookup():
    """Load the charger data."""
    return openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1")


@pytest.fixture(name="test_lookup_missing_loc")
def test_lookup_missing_loc():
    """Load the charger data."""
    return openeihttp.Rates(api="fakeAPIKey")


@pytest.fixture(name="test_lookup_address")
def test_lookup_address():
    """Load the charger data."""
    return openeihttp.Rates(api="fakeAPIKey", address="12345")


@pytest.fixture(name="test_lookup_radius")
def test_lookup_radius():
    """Load the charger data."""
    return openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1", radius="20")


@pytest.fixture(name="test_lookup_tier_low")
def test_lookup_tier_low():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey",
        reading="5.1",
        plan="574613aa5457a3557e906f5b",
    )


@pytest.fixture(name="test_lookup_tier_med")
def test_lookup_tier_med():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey",
        reading="10.3",
        plan="574613aa5457a3557e906f5b",
    )


@pytest.fixture(name="test_lookup_tier_high")
def test_lookup_tier_high():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey",
        reading="40.1",
        plan="574613aa5457a3557e906f5b",
    )


@pytest.fixture(name="test_lookup_monthly_tier_low")
def test_lookup_monthly_tier_low():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey",
        reading="114",
        plan="574613aa5457a3557e906f5b",
    )


@pytest.fixture(name="test_lookup_monthly_tier_med")
def test_lookup_monthly_tier_med():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey",
        reading="301",
        plan="574613aa5457a3557e906f5b",
    )


@pytest.fixture(name="test_lookup_monthly_tier_high")
def test_lookup_monthly_tier_high():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey",
        reading="1300",
        plan="574613aa5457a3557e906f5b",
    )


@pytest.fixture(name="test_rates")
def test_rates():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey", lat="1", lon="1", plan="574613aa5457a3557e906f5b"
    )


@pytest.fixture(name="test_rates_address")
def test_rates_address():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey", address="12345", plan="574613aa5457a3557e906f5b"
    )
