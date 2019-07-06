#!/usr/bin/env python
#
# Copyright (C) 2017 Shoichi Sakane <sakane@tanu.org>, All rights reserved.
# See the file LICENSE in the top level directory for more details.

import sys
import os   # getenv() for extending PYTHONPATH.
import json
import logging
from functools import wraps
from bottle import Bottle, GeventServer, request, abort
from gevent import monkey; monkey.patch_all()
from importlib import import_module
from argparse import ArgumentParser

KEY_TOPOBJ = "DevEUI_uplink"
KEY_TIME = "Time"
KEY_PAYLOAD_HEX = "payload_hex"
KEY_DEVEUI = "DevEUI"
KEY_APP_DATA = "__app_data"

CONF_MODULE_PATH = "module_path"
CONF_SENSORS = "sensors"
CONF_SENSOR_DESC = "desc"
CONF_SENSOR_HANDLER = "handler"
CONF_HANDLERS = "handlers"
CONF_PARSER = "parser"
CONF_DB = "db"
CONF_DB_CONN = "connector"
CONF_DB_ARGS = "args"
CONF_SERVER_ADDR = "server_addr"
CONF_SERVER_PORT = "server_port"
CONF_SERVER_CERT = "server_cert"
CONF_DEBUG_LEVEL = "debug_level"
CONF_OPT_DEBUG = "opt_debug"
CONF_TZ = "tz"

LOG_FMT = "%(asctime)s.%(msecs)d %(lineno)d %(message)s"
LOG_DATE_FMT = "%Y-%m-%dT%H:%M:%S"

app = Bottle()
handler_map = {}

@app.route("/up", method="POST")
def app_up():
    log_common(request)
    if config[CONF_DEBUG_LEVEL] > 1:
        payload = request.body.read()
        logger.debug("---BEGIN OF REQUESTED HEADER---")
        for k,v in request.headers.items():
            logger.debug("{}: {}".format(k,v))
        logger.debug("---END OF REQUESTED HEADER---")
        logger.debug("---BEGIN OF REQUESTED DATA---")
        logger.debug(payload)
        logger.debug("---END OF REQUESTED DATA---")
        request.body.seek(0)
    # convert the payload into JSON.
    try:
        kv_data = json.load(request.body)
    except json.decoder.JSONDecodeError as e:
        emsg = "The payload format was not likely JSON."
        logger.error("{}: {}".format(emsg, e))
        abort(404, emsg)
    #
    kv_root = kv_data.get(KEY_TOPOBJ)
    if not kv_root:
        emsg = "Key {} does not exist in the request.".format(KEY_TOPOBJ)
        logger.error("{}".format(emsg))
        abort(404, emsg)
    #
    ret = proc_tp_uplink(kv_root)
    if ret:
        abort(ret)
    return "OK"

def proc_tp_uplink(kv_data):
    """
    kv_data is a Python object, which is seriaized of the JSON-like string
    of KEY_TOPOBJ sent by a TP NS.
    assuming that all required keys exist in the config.
    """
    # get deveui
    deveui = kv_data.get(KEY_DEVEUI)
    if not deveui:
        logger.error("Key {} does not exist in the request.".format(KEY_DEVEUI))
        return 400  # bad request.
    # get payload_hex
    payload_hex = kv_data.get(KEY_PAYLOAD_HEX)
    if not payload_hex:
        logger.error("Key {} does not exist in the request."
                     .format(KEY_PAYLOAD_HEX))
        return 400  # bad request.
    # get time, for processing later.
    kv_time = kv_data.get(KEY_TIME)
    if not kv_time:
        logger.error("key {} does not exist in the request.".format(KEY_TIME))
        return 400  # bad request.
    #
    logger.info("Received data from {}".format(deveui))
    #
    # get the parser.
    sensor_def = config[CONF_SENSORS].get(deveui)
    if not sensor_def:
        logger.error("DevEUI {} is not defined in the config.".format(deveui))
        return 403  # not found.
    """
    call parser.parse() to try converting the payload_hex.
    if succeeded, it is set into KEY_APP_DATA.
    """
    handler_name = sensor_def.get(CONF_SENSOR_HANDLER)
    handler = handler_map[handler_name]
    logger.debug("Applied Handler: {}".format(handler_name))
    if handler.parser:
        kv_payload = handler.parser.parse_hex(payload_hex)
    else:
        kv_payload = payload_hex
    """
    return value of parser.paser():
        None: ignore parsing.
        False: something error.
        Others: a Python dict should be put in KEY_APP_DATA.
    """
    if kv_payload is None:
        logger.debug("The parser returned None.")
        pass
    elif kv_payload is False:
        # if kv_payload is False variants except of None, then error.
        logger.error("Parsing payload for DevEUI {} failed.".format(deveui))
        return 400  # bad request.
    else:
        kv_data[KEY_APP_DATA] = kv_payload
        if handler.db_conn:
            logger.debug("db_submit() has been called.")
            handler.db_conn.db_submit(kv_data)
    return 0

def log_common(request):
    logger.info("Access from {} {} {}".format(request.remote_addr,
                                              request.method, request.url))

def set_logger(prog_name="", log_file=None, logging_stdout=False,
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
    logger = logging.getLogger(prog_name)
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
    # extend PYTHONPATH
    python_paths = os.getenv("PYTHONPATH")
    if python_paths:
        for p in python_paths.split(":"):
            sys.path.append("{}/parsers".format(p))
            sys.path.append("{}/db_connectors".format(p))
    # set PYTHONPATH
    #for i in config.get(CONF_MODULE_PATH, []):
    #    sys.path.append(i)
    # check if the sensors key exists.
    sensors = config.get(CONF_SENSORS)
    if not sensors:
        print("ERROR: Key {} does not exist in the config."
              .format(CONF_SENSORS))
        return False
    # check if the handlers key exists.
    handlers = config.get(CONF_HANDLERS)
    if not handlers:
        print("ERROR: Key {} does not exist in the config."
              .format(CONF_HANDLERS))
        return False
    #
    config.setdefault(CONF_SERVER_ADDR, "::")
    config.setdefault(CONF_SERVER_PORT, "18886")
    config.setdefault(CONF_SERVER_CERT, None)
    config.setdefault(CONF_TZ, "Asia/Tokyo")
    # overwrite the debug level if opt.debug is True.
    if debug_mode == True:
        config[CONF_DEBUG_LEVEL] = 99
    #
    # NOTE: below check should be placed at the end of this method.
    # check if the handlers are properly defined.
    for deveui,defs in sensors.items():
        handler_name = defs.get(CONF_SENSOR_HANDLER)
        if handler_name is None:
            print("ERROR: sensor {} doesn't have handler.".format(deveui))
            return False
        handler = handlers.get(handler_name)
        if not handler:
            print("ERROR: handler for {} is not defined in the config."
                  .format(deveui))
            return False
        #
        parser_handler = None
        parser_name = handler.get(CONF_PARSER)
        if parser_name:
            try:
                mod = import_module("parser_{}".format(parser_name))
            except Exception as e:
                print("ERROR: importing parser failed for {}, {}"
                      .format(parser_name, e))
                return False
            parser_handler = mod.parser(
                    logger=logger,
                    debug_level=config[CONF_DEBUG_LEVEL])
        #
        db_handler = None
        if handler.get(CONF_DB):
            db_conn_name = handler.get(CONF_DB).get(CONF_DB_CONN)
            if not db_conn_name:
                print("ERROR: {} for {} is not defined."
                      .format(CONF_DB_CONN, handler_name))
                return False
            try:
                mod = import_module("db_connector_{}".format(db_conn_name))
            except Exception as e:
                print("ERROR: importing db_connector failed for {}, {}"
                        .format(db_conn_name, e))
                return False
            db_handler = mod.db_connector(
                    logger=logger,
                    tz=config[CONF_TZ],
                    debug_level=config[CONF_DEBUG_LEVEL],
                    **handler[CONF_DB][CONF_DB_ARGS])
        #
        handler_map[handler_name] = type("handler", (object,), {})
        handler_map[handler_name].parser = parser_handler
        handler_map[handler_name].db_conn = db_handler
    return True

"""
main
"""
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
logger = set_logger(prog_name="SSAS", log_file=config.get("log_file"),
                    logging_stdout=opt.logging_stdout,
                    debug_mode=opt.debug)
if not check_config(config):
    print("ERROR: error in {}.".format(opt.config_file))
    exit(1)
#
server_addr = config.get("server_addr")
server_port = int(config.get("server_port"))
server_cert = config.get("server_cert")
server_scheme = "https" if server_cert else "http"
logger.info("Starting the SSAS listening on {}://{}:{}/"
            .format(server_scheme,
                    server_addr if server_addr else "0.0.0.0",
                    server_port))
#
if server_cert:
    app.run(host=server_addr, port=server_port,
            certfile=server_cert,
            server=GeventServer, quiet=True, debug=False)
else:
    app.run(host=server_addr, port=server_port,
            server=GeventServer, quiet=True, debug=False)
