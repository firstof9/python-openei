import re
from unittest.mock import patch

import pytest
from yarl import URL

import openeihttp

pytestmark = pytest.mark.asyncio


class MockResponse:
    """Mock aiohttp response."""

    def __init__(self, status: int, text: str) -> None:
        """Initialize."""
        self.status = status
        self._text = text

    async def text(self) -> str:
        """Return text."""
        return self._text

    async def read(self) -> bytes:
        """Return bytes."""
        return self._text.encode("utf-8")

    async def __aenter__(self):
        """Enter context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        pass


class AiohttpClientMocker:
    """Mock aiohttp client requests."""

    def __init__(self) -> None:
        """Initialize."""
        self.mocks = []
        self._patcher = patch("aiohttp.ClientSession._request", side_effect=self._mock_request)

    def get(self, url, status=200, body="", repeat=False, exception=None, **kwargs) -> None:
        """Register a mock GET request."""
        self.mocks.append(
            {
                "method": "GET",
                "url": url,
                "status": status,
                "body": body,
                "repeat": repeat,
                "exception": exception,
            }
        )

    def start(self) -> None:
        """Start patching."""
        self._patcher.start()

    def stop(self) -> None:
        """Stop patching."""
        self._patcher.stop()

    async def _mock_request(self, method, url, *args, **kwargs):
        """Intercept and mock requests."""
        params = kwargs.get("params")
        url_str = str(URL(url).with_query(params)) if params else str(url)

        for mock in self.mocks:
            if mock["method"] == method:
                pattern = mock["url"]
                matched = False
                if isinstance(pattern, re.Pattern):
                    if pattern.search(url_str):
                        matched = True
                elif pattern == url_str:
                    matched = True

                if matched:
                    if not mock["repeat"]:
                        self.mocks.remove(mock)
                    if mock["exception"] is not None:
                        raise mock["exception"]
                    return MockResponse(mock["status"], mock["body"])
        raise AssertionError(f"No mock registered for {method} {url_str}")


@pytest.fixture
def mock_aioclient():
    """Fixture to mock aioclient calls."""
    mocker = AiohttpClientMocker()
    mocker.start()
    yield mocker
    mocker.stop()


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


@pytest.fixture(name="test_rates")
def test_rates():
    """Load the charger data."""
    return openeihttp.Rates(api="fakeAPIKey", lat="1", lon="1", plan="574613aa5457a3557e906f5b")


@pytest.fixture(name="test_rates_address")
def test_rates_address():
    """Load the charger data."""
    return openeihttp.Rates(api="fakeAPIKey", address="12345", plan="574613aa5457a3557e906f5b")
