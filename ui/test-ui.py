#!/usr/bin/env python

import asyncio
from aiohttp import web
import aiohttp
import logging

# for client IO
from aiohttp import ClientSession
import json
import os   # file check.
import ssl

from datetime import datetime
import argparse

LOG_FMT = "%(asctime)s.%(msecs)d %(lineno)d %(message)s"
LOG_DATE_FMT = "%Y-%m-%dT%H:%M:%S"

async def client_ws_ui(ws):
    try:
        msg = await ws.receive(timeout=1)
    except asyncio.TimeoutError:
        return True
    logging.debug("type", msg.type)
    if msg.type == aiohttp.WSMsgType.TEXT:
        print("received:", msg.data)
        # XXX
        await ws.send_str(json.dumps({
                "msg_type":"response",
                "result":{
                        "timestamp":datetime.now().isoformat(),
                        "status":"queued"
                        }}))
        return True
    elif msg.type == aiohttp.WSMsgType.ERROR:
        print("ws connection closed with exception %s" %
                ws.exception())
        return False

async def send_downlink(message):

    # XXX should verify the data.
    deveui = "00137A1000005734"
    fport = 7
    hex_msg = "0011"
    confirmed = False
    flush_queue = True

    url = f'{opt.dxapi_url}/devices/{deveui}/downlinkMessages'
    headers = {
        "Content-Type":"application/json",
        "Accept":"application/json",
        "Authorization":"Bearer " + opt.raw_token,
        }
    body = {
        "payloadHex" : hex_msg,
        "targetPorts" : fport,
        "confirmDownlink": confirmed,
        "flushDownlinkQueue": flush_queue,
        "securityParams": {
            "asId": opt.asid,
            "asKey": opt.askey
            }
        }
    logger.debug("URL: {}".format(url))
    logger.debug("HEADER: {}".format(headers))
    logger.debug("BODY: {}".format(body))

    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    async with ClientSession() as session:
        async with session.post(url, json=body, headers=headers,
                                ssl=ctx) as resp:
            logger.debug("waiting for a response from DX-API.  deveui={}"
                         .format(deveui))
            print(resp.status)
            result = await resp.text()
            # XXX do verify the result.
            loogger.debug("received a response from DX-API. deveui={}"
                          .format(deveui))
            print(result)
            return web.json_response({"result":"queued."})

#
# WS I/O
#
async def ws_handler(request):
    """
    return value in json string.
        - "msg_type": "app_data"
            {
                "msg_type": "app_data", # required.
                "timestamp": "...",     # required.
                "dev_eui": "...",       # required.
                "dev_name": "xxx",      # taken from config.
                "lat": "...",
                "lon": "...",
                "app_data": {           # required.
                    "rssi": "xxx",      # required.
                    "snr": "xxx",       # required.
                    "hex_data": "xxx",  # required, taken from the UL payload.
                    "key1": "value1",
                    "key2": "value2",
                    ...
                }
            }
        - "msg_type": "response"
            {
                "msg_type": "response", # required.
                "timestamp": "...",     # required.
                "result": {             # required.
                    "key1": "value1",   # required.
                    "key2": "value2",
                    ...
                }
            }
    """
    ws = web.WebSocketResponse()
    ret = await ws.prepare(request)
    logger.debug("ws session starts with:", request)

    while True:
        #result await yah(ws)
        result = await client_ws_ui(ws)
        if not result:
            await ws.close()
            break

    logger.debug("ws session closed")
    return ws

#
# REST API
#
async def downlink_handler(request):
    if not request.can_read_body:
        return web.json_response({"result":"failed. no body"})
    #
    body = await request.json()
    logger.debug("accepted downlink request: {}".format(body))

    await send_downlink(body)

async def get_doc_handler(request):
    path = ".{}".format(request.path)
    logger.debug("DEBUG: serving {}".format(path))
    if os.path.exists(path):
        return web.FileResponse(path)
    else:
        raise web.HTTPNotFound()

#
# misc
#
def set_logger(log_file=None, logging_stdout=False,
               debug_mode=False):
    # XXX need to review this set_logger() code.
    def get_logging_handler(channel, debug_mode):
        channel.setFormatter(logging.Formatter(fmt=LOG_FMT,
                                               datefmt=LOG_DATE_FMT))
        if debug_mode:
            channel.setLevel(logging.DEBUG)
        else:
            channel.setLevel(logging.INFO)
        return channel
    #
    # set logger.
    #   log_file: a file name for logging.
    logging.basicConfig()
    logger = logging.getLogger()
    if logging_stdout is True:
        logger.addHandler(get_logging_handler(logging.StreamHandler(),
                                              debug_mode))
    if log_file is not None:
        logger.addHandler(get_logging_handler(logging.FileHandler(log_file),
                                              debug_mode))
    if debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger

#
# main
#
ap = argparse.ArgumentParser(
        description="a downloader for lorawan ssas.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("-p", action="store", dest="http_port", default="65486",
                help="specify a port number to serve the data.")
ap.add_argument("-l", action="store", dest="log_file",
                help="specify a file name for logging.")
ap.add_argument("--server-cert", action="store", dest="server_cert",
                help="specify a certificate for this server.")
ap.add_argument("-d", action="store_true", dest="debug",
                help="enable debug mode.")
ap.add_argument("-D", action="store_true", dest="logging_stdout",
                help="enable to show messages onto stdout.")
opt = ap.parse_args()

# XXX for test
opt.dxapi_url = "https://tpe-iictokyo.actility.local/thingpark/dx/core/latest/api"
opt.asid = "TWA_1100000000.8.AS"
opt.askey = "4abf5f2fcb2e958469495602f3ba8016"
opt.raw_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzY29wZSI6WyJTVUJTQ1JJQkVSOjEwMDAwMDAwMCJdLCJleHAiOjM3Mjc1OTY0OTIsImp0aSI6IjAzMWJkZmY5LTZlMzctNDVmZS1hOTc0LWU2ZTZjYmEzMzkxOCIsImNsaWVudF9pZCI6InRwZS1hcGkvc3Nha2FuZUBjaXNjby5jb20ifQ.koyVnNlhQ3Y8MI5aFMEuQU5sTVSGBDPZIkPyaYM0Hqz0tElPk71WctLliRhKCD6ioep5zhjr0Mo4sTqWONNMDA"

opt.ws_port = 5678

# set logger.
logger = set_logger(log_file=opt.log_file,
                    logging_stdout=opt.logging_stdout,
                    debug_mode=opt.debug)
# XXX the files provided should be fixed.
app = web.Application(logger=logger)
app.router.add_route("POST", "/dl", downlink_handler)
app.router.add_route("GET", "/ws", ws_handler)
app.router.add_route("GET", "/{tail:.*}", get_doc_handler)
# making ssl context.
if opt.server_cert:
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(opt.server_cert)
    server_schema = "https"
else:
    ssl_context = None
    server_schema = "http"
# start the loop.
loop = asyncio.get_event_loop()
loop.set_debug(opt.debug)
logger.debug(f"start {server_schema} server on {opt.http_port}")

#web.run_app(app, host="0.0.0.0", port=opt.http_port, ssl_context=ssl_context)
handler = app.make_handler()
f = loop.create_server(handler, host="0.0.0.0", port=opt.http_port,
                       ssl=ssl_context)
srv = loop.run_until_complete(f)
print("serving on", srv.sockets[0].getsockname())
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.run_until_complete(handler.finish_connections(1.0))
    srv.close()
    loop.run_until_complete(srv.wait_closed())
    loop.run_until_complete(app.finish())
loop.close()
