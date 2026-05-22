"""Provide a package for python-openei."""

from .client import Rates
from .exceptions import (
    APIError,
    InvalidCall,
    NotAuthorized,
    RateLimit,
    UrlNotFound,
)

__all__ = [
    "Rates",
    "APIError",
    "InvalidCall",
    "NotAuthorized",
    "RateLimit",
    "UrlNotFound",
]
