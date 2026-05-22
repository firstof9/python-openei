"""Constants for python-openei."""

BASE_URL = "https://api.openei.org/utility_rates"
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
}
ERROR_TIMEOUT = "Timeout while updating"
MIN_CACHE_SIZE = 194  # Minimum size for a valid JSON cache file from OpenEI
