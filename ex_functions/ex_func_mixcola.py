import asyncio
import aiohttp
import textwrap

# self.url_get is a url of the text data to send back to the device.
URL_GET = "https://localhost:18886/test.txt"
verify = False

class ex_handler():
    def __init__(self, logger, debug_level, **kwargs):
        self.logger = logger
        self.debug_level = debug_level
        self.url_get = URL_GET
        self.url_post = "https://localhost:18886/dl"

    async def run(self, deveui, data, **kwargs):
        task = asyncio.create_task(self.doit(deveui, data))
        await task

    async def doit(self, deveui, data, **kwargs):
        if verify == True:
            conn = None
        else:
            conn = aiohttp.TCPConnector(verify_ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(self.url_get) as response:
                # assuming plain/text.
                text = await response.text()
                self.logger.debug(text)

        if len(text) > 500:
            raise ValueError("ERROR: ex_handler: too large text > 500.")

        for t in textwrap.wrap(text, 50):
            kv_data = {
                    "deveui": deveui,
                    "hex_data": bytes(t, encoding="utf-8").hex(),
                    "fport": "1",
                    "confirmed": False,
                    "flush_queue": False
                    }

            if verify == True:
                conn = None
            else:
                conn = aiohttp.TCPConnector(verify_ssl=False)
            async with aiohttp.ClientSession(connector=conn) as session:
                async with session.post(self.url_post, json=kv_data) as response:
                    # assuming application/json.
                    ret = await response.json()
                    self.logger.debug(ret)
