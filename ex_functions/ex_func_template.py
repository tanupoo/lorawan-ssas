import asyncio
import aiohttp

class ex_handler():
    def __init__(self, logger, debug_level, **kwargs):
        self.logger = logger
        self.debug_level = debug_level

    async def ex_run(self, deveui, data, **kwargs):
        """
        TEMPLATE should be overwritten.
        - execute something with deveui, data, and kwargs.
        - the return value should be:
            + None: ignore parsing.
            + False: something error.
            + True: succeeded.
        """
        return True
