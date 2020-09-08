#!/usr/bin/env python
#
# Copyright (C) 2017-2020 Shoichi Sakane <sakane@tanu.org>, All rights reserved.
# See the file LICENSE in the top level directory for more details.

import sys
import os   # getenv() for extending PYTHONPATH.
import json
import logging
import asyncio
from aiohttp import web
import aiohttp
import logging
import ssl
from importlib import import_module
from argparse import ArgumentParser
from datetime import datetime
from app_util import iso8601_to_fixed_ts

KEY_APP_DATA = "app_data"

CONF_SENSORS = "sensors"
CONF_SENSOR_DESC = "desc"
CONF_SENSOR_PARSER = "parser"
CONF_SENSOR_NAME = "name"
CONF_SENSOR_HANDLERS = "handlers"
CONF_SENSOR_DB_HANDLER = "db_handler"
CONF_SENSOR_EX_HANDLER = "ex_handler"
CONF_NS_HANDLER = "ns_handler"
CONF_NS_CONNECTOR = "connector"
CONF_NS_ARGS = "args"
CONF_DB_HANDLERS = "db_handlers"
CONF_DB_CONNECTOR = "connector"
CONF_DB_ARGS = "args"
CONF_SERVER_ADDR = "server_addr"
CONF_SERVER_PORT = "server_port"
CONF_SERVER_CERT = "server_cert"
CONF_DEBUG_LEVEL = "debug_level"
CONF_OPT_DEBUG = "opt_debug"
CONF_TZ = "tz"
CONF_DIR_PARSERS = "parsers"
CONF_DIR_DB_CONNS = "db_connectors"
CONF_DIR_NS_CONNS = "ns_connectors"
CONF_DIR_EX_FUNCS = "ex_functions"
CONF_DEFAULT_SERVER_PORT = "18886"
SSL_CTX = "__ssl_ctx"
NS_CONN = "__ns_conn"
SENSOR_HANDLER = "__sh"

LOG_FMT = "%(asctime)s.%(msecs)d %(lineno)d %(message)s"
LOG_DATE_FMT = "%Y-%m-%dT%H:%M:%S"

ws_map = {}

#
# utilities
#
def common_access_log(request):
    logger.info("Access from {} {} {}".format(request.remote,
                                              request.message.method,
                                              request.message.url))

def gen_http_response(msg, status=200, log_text=None):
    res_msg = gen_common_response(msg, status=200, log_text=log_text)
    return web.json_response(res_msg, status=status)

async def send_ws_response(ws, msg, status=200, log_text=None):
    res_msg = gen_common_response(msg, status=200, log_text=log_text)
    await ws.send_str(json.dumps(res_msg))

def gen_common_response(msg, status=200, log_text=None):
    """
    msg: json object such string or dict.
    send below json string.
        {
            "msg_type": "response", # required.
            "status": status,       # required.
            "ts": "...",     # required.
            "result": msg           # required.
        }
    """
    if status != 200:
        logger.error("{} status={} error={}".format(msg, status, log_text))
    else:
        logger.debug("{} status={}".format(msg, status))
    #
    return {
            "msg_type": "response",
            "status": status,
            "ts": datetime.now().isoformat(),
            "result": msg }

#
# WS I/O
#
async def ws_handler(request):
    common_access_log(request)
    ws = web.WebSocketResponse()
    ret = await ws.prepare(request)
    logger.debug("ws session starts with:", request)
    # register this session.
    if ws_map.get(ws):
        # just remove the old one.
        ws_map.pop(ws)
    ws_map.setdefault(ws, { "deveui": None })
    #
    # main loop.
    while True:
        #result await yah(ws)
        result = await client_ws_ui(ws)
        if not result:
            await ws.close()
            break
    #
    # here, close this session.
    ws_map.pop(ws)
    logger.debug("ws session closed")
    return

async def client_ws_ui(ws):
    """
    expecting message from a client:
        - register a set of DevEUI interested.
            {
                "msg_type": "register",
                "deveui": [ "...", "..." ]
            }
        - downlink
            {
                "msg_type": "downlink",
                "...",
                "hex_data": "..."
            }
    return value in json string.
        - "msg_type": "uplink"
            {
                "msg_type": "uplink",   # required.
                "dev_name": "...",      # taken from config.
                "app_data": {           # required.
                    "deveui": "...",    # required.
                    "_ts": "...",        # required.
                    "_gw_rssi": "...",   # required.
                    "_gw_snr": "...",    # required.
                    "_gw_lat": "...",    # required.
                    "_gw_lon": "...",    # required.
                    "hex_data": "...",  # required, taken from the UL payload.
                    "key1": "value1",
                    "key2": "value2",
                    ...
                }
            }
        - "msg_type": "response"
            {
                "msg_type": "response", # required.
                "ts": "...",     # required.
                "result": {             # required.
                    "key1": "value1",   # required.
                    "key2": "value2",
                    ...
                }
            }
    """
    try:
        msg = await ws.receive(timeout=1)
    except asyncio.TimeoutError:
        # timeout
        return True
    logging.debug(f"ws received: type {msg.type}")
    if msg.type == aiohttp.WSMsgType.TEXT:
        logger.debug("received ws data:" , msg.data)
        kv_data = json.loads(msg.data)
        if kv_data["msg_type"] == "register":
            deveui = kv_data.get("deveui")
            if not deveui:
                await send_ws_response(ws, "key deveui wasn't specified.",
                                       status=400)
            else:
                ws_map[ws]["deveui"] = deveui
                logging.info(f"deveui registered: {deveui}")
                await send_ws_response(ws, "registered", status=200)
            return True
        elif kv_data["msg_type"] == "downlink":
            await config[NS_CONN].send_downlink(kv_data)
            await send_ws_response(ws, "queued", status=200)
        else:
            await send_ws_response(ws, "unknown message", status=400)
        # XXX
        return True
    elif msg.type == aiohttp.WSMsgType.ERROR:
        logging.error("ws connection closed with exception {}"
                      .format(ws.exception()))
        return False

#
# REST API
#
async def downlink_handler(request):
    """
    ideally, downlink handler should be defined for each device.
    """
    common_access_log(request)
    if not request.can_read_body:
        return web.json_response({"result":"failed. no readable body"})
    #
    if request.content_type == "text/plain":
        kv_data = await request.text()
    elif request.content_type == "application/json":
        kv_data = await request.json()
    else:
        return web.json_response(
                {"result":
                 f"failed. unsupported content-type, {request.content_type}"})
    logger.debug("accepted downlink request: {}".format(kv_data))
    loop.call_soon(do_downlink, kv_data)
    return web.json_response({"result":"accepted"})

async def do_downlink_coro(kv_data):
    await config[NS_CONN].send_downlink(kv_data)

def do_downlink(kv_data):
    asyncio.ensure_future(do_downlink_coro(kv_data))

async def get_doc_handler(request):
    """
    all document must be placed under the ui directory.
    """
    common_access_log(request)
    path = "./ui/{}".format(request.path)
    logger.debug("DEBUG: serving {}".format(path))
    if os.path.exists(path):
        return web.FileResponse(path)
    else:
        raise web.HTTPNotFound()

async def uplink_handler(request):
    common_access_log(request)
    if not request.can_read_body:
        return web.json_response({"result":"failed. no readable body"})
    if config[CONF_DEBUG_LEVEL] > 1:
        # header
        logger.debug("---HEADER---")
        for k,v in request.headers.items():
            logger.debug("{}: {}".format(k,v))
        # body
        t = await request.read()
        if isinstance(t, bytes):
            t = t.decode("utf-8")
        elif isinstance(t, str):
            pass
        else:
            return gen_http_response(
                    "The payload type is neigther bytes nor str. {}"
                    .format(type(t)),
                    status=404)
        logger.debug("---BODY---")
        logger.debug(t)
        logger.debug("---END---")
    # read json.
    try:
        content = await request.json()
    except json.decoder.JSONDecodeError as e:
        return gen_http_response(
                "The payload format was not likely JSON.",
                status=404, log_text=str(e))
    # get data object.
    kv_data, log_text = config[NS_CONN].gen_common_data(content)
    if kv_data is None:
        logger.info(log_text)
        return gen_http_response(
            "no data object was found.",
            status=400) # bad request
    #
    deveui = kv_data["deveui"]
    logger.info(f"Received uplink data from {deveui}")
    # parse the hex_data.
    dev_def = config[CONF_SENSORS].get(deveui)
    if not dev_def:
        return gen_http_response(
            f"DevEUI {deveui} is not defined in the config.",
            status=403) # not found.
    """
    call parser.parse() to try converting the hex_data.
    if succeeded, it is set into KEY_APP_DATA.
    """
    kv_data[KEY_APP_DATA] = None
    sh = dev_def[SENSOR_HANDLER]
    if sh.parser:
        kv_data[KEY_APP_DATA] = sh.parser.parse_hex(kv_data["hex_data"])
    """
    return value of parser.paser():
        None: ignore parsing by the parser.
        False: something error.
        Others: a Python dict should be put in KEY_APP_DATA.
    """
    if kv_data[KEY_APP_DATA] is None:
        logger.debug(f"hex_data for {deveui} is not parsed by some reasons.")
    elif not kv_data[KEY_APP_DATA]:
        # if kv_payload is False variants except of None, then error.
        return gen_http_response(
                f"parsing hex_data for {deveui} failed.",
                status=400)  # bad request.
        # thru here, and process for WS later if needed.
    else:
        # fix app_data
        kv_data.update(kv_data[KEY_APP_DATA].copy())
    kv_data.pop(KEY_APP_DATA)
    logger.debug(f"kv_data: {kv_data}")
    # submit data into database if needed.
    if sh.db_conn:
        logger.debug("db_submit() will be called.")
        if sh.db_conn.db_submit(kv_data):
            logger.info(f"Submited data for {deveui} successfully.")
        # even if error, proceed next anyway.
        # remove ObjectID("...") from kv_data as MongoDB adds "_id":ObjectID().
        if kv_data.get("_id"):
            kv_data.pop("_id")
    # call ex_run() if needed.
    if sh.ex_func:
        logger.debug("ex_run() will be called.")
        if await sh.ex_func.ex_run(deveui, kv_data):
            logger.info(f"executed ex_func for {deveui} successfully.")
    # WS processing if needed.
    """
    if the deveui has been registered in ws_map, it try to send the data to the
    WS node registered.
    """
    if len(ws_map) != 0:
        logger.debug("start WS processing: nb_client={}".format(len(ws_map)))
        ws_uplink_msg = json.dumps({
                "msg_type": "uplink",
                "dev_name": dev_def.get(CONF_SENSOR_NAME),
                "app_data": kv_data
                })
        for ws, x in ws_map.items():
            if deveui == x["deveui"]:
                print(ws)
                logger.info(f"send uplink from {deveui}")
                try:
                    await ws.send_str(ws_uplink_msg)
                except Exception as e:
                    print(e)
    #
    return gen_http_response("success")

#
# configuration
#
def set_logger(log_file=None, logging_stdout=False,
               debug_mode=False):
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

def check_config(config, debug_mode=False):
    # overwrite the debug level if opt.debug is True.
    if debug_mode == True:
        config[CONF_DEBUG_LEVEL] = 99
    # add the module's path.
    # assumed the 1st path in sys.path is the ssas directory.
    ssas_path = sys.path[0]
    for p in [ CONF_DIR_PARSERS, CONF_DIR_DB_CONNS, CONF_DIR_NS_CONNS,
              CONF_DIR_EX_FUNCS ]:
        mp = os.path.join(ssas_path, p)
        if not os.path.exists(mp):
            logger.error(f"{mp} doesn't exist.")
            return False
        sys.path.insert(0, mp)
    logger.debug(f"expanded sys.path={sys.path}")
    # set the access point of the server.
    config.setdefault(CONF_SERVER_ADDR, "::")
    config.setdefault(CONF_SERVER_PORT, CONF_DEFAULT_SERVER_PORT)
    config[CONF_SERVER_PORT] = int(config[CONF_SERVER_PORT])
    config.setdefault(CONF_TZ, "Asia/Tokyo")
    config.setdefault(CONF_SERVER_CERT, None)
    # make ssl context.
    logger.debug(f"cert specified: {config.get(CONF_SERVER_CERT)}")
    if config.get(CONF_SERVER_CERT):
        config[SSL_CTX] = ssl.create_default_context(
                ssl.Purpose.CLIENT_AUTH)
        config[SSL_CTX].load_cert_chain(config[CONF_SERVER_CERT])
    # check if the handlers exists.
    sensor_def_block = config.get(CONF_SENSORS)
    if not sensor_def_block:
        logger.error(f"Key {CONF_SENSORS} does not exist in the config.")
        return False
    db_def_block = config.get(CONF_DB_HANDLERS)
    if not db_def_block:
        logger.error(
                f"Key {CONF_DB_HANDLERS} does not exist in the config.")
        return False
    # setup ns connector.
    ns_def_block = config.get(CONF_NS_HANDLER, {})
    if ns_def_block != {}:
        ns_conn_name = ns_def_block.get(CONF_NS_CONNECTOR)
        if not ns_conn_name:
            logger.error(f"{CONF_NS_CONNECTOR} in {ns_def_block} is not defined.")
            return False
        try:
            mod = import_module(f"ns_connector_{ns_conn_name}")
        except Exception as e:
            logger.error("importing ns_connector {} failed. {}"
                    .format(ns_conn_name, e))
            return False
        ns_args = ns_def_block.get(CONF_NS_ARGS, {})
        config[NS_CONN] = mod.ns_connector(
                logger=logger,
                tz=config[CONF_TZ],
                debug_level=config[CONF_DEBUG_LEVEL],
                **ns_args)
    # check if the parameters are properly defined.
    # NOTE: below check should be placed at the end of this function.
    for deveui,dev_def in sensor_def_block.items():
        # create a place holder of the handlers for the device.
        dev_def[SENSOR_HANDLER] = type(SENSOR_HANDLER, (object,), {})
        dev_def[SENSOR_HANDLER].parser = None
        dev_def[SENSOR_HANDLER].db_conn = None
        dev_def[SENSOR_HANDLER].ex_func = None
        # setup parser.
        parser_name = dev_def.get(CONF_SENSOR_PARSER)
        if parser_name:
            try:
                mod = import_module("parser_{}".format(parser_name))
            except Exception as e:
                print("ERROR: importing parser failed for {}, {}"
                      .format(parser_name, e))
                return False
            dev_def[SENSOR_HANDLER].parser = mod.parser(
                    logger=logger,
                    debug_level=config[CONF_DEBUG_LEVEL])
        # setup handlers.
        hdl_list = dev_def.get(CONF_SENSOR_HANDLERS)
        if hdl_list is not None and len(hdl_list) > 0:
            for hdl_type,hdl_name in hdl_list.items():
                if hdl_type == CONF_SENSOR_DB_HANDLER and hdl_name:
                    db_hdl = db_def_block.get(hdl_name)
                    if not db_hdl:
                        logger.error(f"db handler for {deveui} is not defined.")
                        return False
                    db_conn_name = db_hdl.get(CONF_DB_CONNECTOR)
                    if not db_conn_name:
                        print(f"ERROR: {CONF_DB_CONNECTOR} for {db_hdl_name} is not defined.")
                        return False
                    try:
                        mod = import_module(f"db_connector_{db_conn_name}")
                    except Exception as e:
                        print("ERROR: importing db_connector failed for {}, {}"
                                .format(db_conn_name, e))
                        return False
                    db_args = db_hdl.get(CONF_DB_ARGS, {})
                    dev_def[SENSOR_HANDLER].db_conn = mod.db_connector(
                            logger=logger,
                            tz=config[CONF_TZ],
                            debug_level=config[CONF_DEBUG_LEVEL],
                            **db_args)
                elif hdl_type == CONF_SENSOR_EX_HANDLER and hdl_name:
                    try:
                        mod = import_module(f"ex_func_{hdl_name}")
                    except Exception as e:
                        logger.error("importing ex_handler {} failed. {}"
                                .format(ns_conn_name, e))
                        return False
                    dev_def[SENSOR_HANDLER].ex_func = mod.ex_handler(
                                        logger=logger,
                                        debug_level=config[CONF_DEBUG_LEVEL])
    return True

#
# main
#
ap = ArgumentParser()
ap.add_argument("config_file", metavar="CONFIG_FILE",
                help="specify the config file.")
ap.add_argument("-d", action="store_true", dest="debug",
               help="enable debug mode.")
ap.add_argument("-D", action="store_true", dest="logging_stdout",
               help="enable to show messages onto stdout.")
opt = ap.parse_args()

# load the config file.
try:
    config = json.load(open(opt.config_file))
except Exception as e:
    print("ERROR: {} read error. {}".format(opt.config_file, e))
    exit(1)
# update config.
config.setdefault(CONF_DEBUG_LEVEL, 0)  # only CONF_DEBUG_LEVEL needs here.
logger = set_logger(log_file=config.get("log_file"),
                    logging_stdout=opt.logging_stdout,
                    debug_mode=opt.debug)
if not check_config(config, debug_mode=opt.debug):
    print("ERROR: error in {}.".format(opt.config_file))
    exit(1)
# enable debug mode
loop = asyncio.get_event_loop()
loop.set_debug(opt.debug)
# make routes.
app = web.Application(logger=logger)
app.router.add_route("POST", "/up", uplink_handler)
app.router.add_route("POST", "/dl", downlink_handler)
app.router.add_route("GET", "/ws", ws_handler)
app.router.add_route("GET", "/{tail:.*}", get_doc_handler)
logger.info("Starting the SSAS listening on {}://{}:{}/"
            .format("https" if config.get(CONF_SERVER_CERT) else "http",
                    config.get(CONF_SERVER_ADDR) if config.get(CONF_SERVER_ADDR) else "*",
                    config.get(CONF_SERVER_PORT)))
# start server
web.run_app(app,
            host=config.get(CONF_SERVER_ADDR),
            port=config.get(CONF_SERVER_PORT),
            ssl_context=config.get(SSL_CTX),
            print=None)

