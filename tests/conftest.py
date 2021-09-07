"""Provide common pytest fixtures."""
import pytest

import openeihttp
from tests.common import load_fixture


@pytest.fixture(name="test_lookup")
def test_lookup():
    """Load the charger data."""
    return openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1")


@pytest.fixture(name="test_lookup_radius")
def test_lookup_radius():
    """Load the charger data."""
    return openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1", radius="20")


@pytest.fixture(name="test_lookup_tier_low")
def test_lookup_tier_low():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey",
        lat="1",
        lon="1",
        radius="20",
        reading="5.1",
        plan="574613aa5457a3557e906f5b",
    )


@pytest.fixture(name="test_lookup_tier_med")
def test_lookup_tier_med():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey",
        lat="1",
        lon="1",
        radius="20",
        reading="10.3",
        plan="574613aa5457a3557e906f5b",
    )


@pytest.fixture(name="test_lookup_tier_high")
def test_lookup_tier_high():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey",
        lat="1",
        lon="1",
        radius="20",
        reading="40.1",
        plan="574613aa5457a3557e906f5b",
    )


@pytest.fixture(name="test_rates")
def test_rates():
    """Load the charger data."""
    return openeihttp.Rates(
        api="fakeAPIKey", lat="1", lon="1", plan="574613aa5457a3557e906f5b"
    )


@pytest.fixture(name="lookup_mock")
def mock_lookup(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential",
        text=load_fixture("lookup.json"),
    )


@pytest.fixture(name="lookup_mock_radius")
def mock_lookup_radius(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential&radius=20",
        text=load_fixture("lookup_radius.json"),
    )


@pytest.fixture(name="plandata_mock")
def mock_plandata(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential&detail=full&getpage=574613aa5457a3557e906f5b",
        text=load_fixture("plan_data.json"),
    )


@pytest.fixture(name="plandata_radius_mock")
def mock_plandata(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential&detail=full&getpage=574613aa5457a3557e906f5b&radius=20",
        text=load_fixture("plan_data.json"),
    )


@pytest.fixture(name="demand_plandata_mock")
def mock_demand_plandata(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential&detail=full&getpage=574613aa5457a3557e906f5b",
        text=load_fixture("plan_demand_data.json"),
    )


@pytest.fixture(name="tier_plandata_mock")
def mock_tier_plandata(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential&detail=full&getpage=574613aa5457a3557e906f5b",
        text=load_fixture("plan_tier_data.json"),
    )


@pytest.fixture(name="lookup_mock_404")
def mock_lookup_404(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential",
        status_code=404,
    )


@pytest.fixture(name="plandata_mock_404")
def mock_plandata_404(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential&detail=full&getpage=574613aa5457a3557e906f5b",
        status_code=404,
    )


@pytest.fixture(name="lookup_mock_401")
def mock_lookup_401(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential",
        status_code=401,
    )


@pytest.fixture(name="plandata_mock_401")
def mock_plandata_401(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential&detail=full&getpage=574613aa5457a3557e906f5b",
        status_code=401,
    )


@pytest.fixture(name="plandata_mock_api_err")
def mock_plandata_api_err(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential&detail=full&getpage=574613aa5457a3557e906f5b",
        text=load_fixture("api_error.json"),
    )


@pytest.fixture(name="lookup_mock_api_err")
def mock_lookup_api_err(requests_mock):
    """Mock the status reply."""
    requests_mock.get(
        "https://api.openei.org/utility_rates?version=latest&format=json&api_key=fakeAPIKey&lat=1&lon=1&sector=Residential",
        text=load_fixture("api_error.json"),
    )
