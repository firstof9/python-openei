""" Cache functions for python-openei."""

import aiofiles
import aiofiles.os
import json
import logging
from os.path import dirname, join
from typing import Any

_LOGGER = logging.getLogger(__name__)

class OpenEICache:
    """ Represent OpenEI Cache manager."""
    def __init__(self, cache_file: str = join(dirname(__file__), 'openei_cache')) -> None:
        """Initialize."""
        self._cache_file = cache_file

    async def write_cache(self, data: Any) -> None:
        """Write cache file."""
        async with aiofiles.open(self._cache_file, mode='wb') as file:
            _LOGGER.debug("Writing file: %s", self._cache_file)
            await file.write(data)

    async def read_cache(self) -> Any:
        """Read cache file."""
        async with aiofiles.open(self._cache_file, mode='r') as file:
            _LOGGER.debug("Reading file: %s", self._cache_file)
            value = await file.read()

            try: 
                verify = json.loads(value)
                return verify
            except json.decoder.JSONDecodeError:
                _LOGGER.info("Invalid JSON data")

            return {}
    
    async def cache_exists(self) -> bool:
        """Return bool if cache exists and contains data."""
        check = await aiofiles.os.path.isfile(self._cache_file)
        if check:
            size = await aiofiles.os.path.getsize(self._cache_file)
            return size > 194
        return False

    async def clear_cache(self) -> None:
        """Remove cache file."""
        if await self.cache_exists():
            await aiofiles.os.remove(self._cache_file)
