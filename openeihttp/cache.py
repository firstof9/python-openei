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
    def __init__(self, path: str = './') -> None:
        """Initialize."""
        self._path = path
        self.filename = "openei_cache"

    async def write_cache(self, data: Any) -> None:
        """Write cache file."""
        full_path = join(dirname(__file__), self._path, self.filename)
        async with aiofiles.open(full_path, mode='wb') as file:
            _LOGGER.debug("Writing file: %s", full_path)
            await file.write(data)

    async def read_cache(self) -> Any:
        """Read cache file."""
        full_path = join(dirname(__file__), self._path, self.filename)
        async with aiofiles.open(full_path, mode='r') as file:
            _LOGGER.debug("Reading file: %s", full_path)
            value = await file.read()

            try: 
                verify = json.loads(value)
                return verify
            except json.decoder.JSONDecodeError:
                _LOGGER.info("Invalid JSON data")

            return {}
    
    async def cache_exists(self) -> bool:
        """Return bool if cache exists and contains data."""
        full_path = join(dirname(__file__), self._path, self.filename)
        check = await aiofiles.os.path.isfile(full_path)
        if check:
            size = await aiofiles.os.path.getsize(full_path)
            return size > 194
        return False

    async def clear_cache(self) -> None:
        """Remove cache file."""
        full_path = join(dirname(__file__), self._path, self.filename)
        if await self.cache_exists():
            await aiofiles.os.remove(full_path)
