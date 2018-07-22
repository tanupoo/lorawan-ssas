#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Shoichi Sakane <sakane@tanu.org>, All rights reserved.
# See the file LICENSE in the top level directory for more details.
#

from __future__ import print_function

import sys
import json
import logging
from functools import wraps
from bottle import Bottle, GeventServer, request, abort
from gevent import monkey; monkey.patch_all()
from importlib import import_module
from argparse import ArgumentParser
#import requests

PROG_NAME = "lrwssas"
KEY_TOPOBJ = "DevEUI_uplink"
KEY_TIME = "Time"
KEY_PAYLOAD_HEX = "payload_hex"
KEY_DEVEUI = "DevEUI"
KEY_APP_DATA = "__app_data"

CONF_MODULE_PATH = "module_path"
CONF_MODULE = "module"
CONF_APP_TYPE = "app_type"
CONF_HANDLERS = "handlers"
CONF_SERVER_ADDR = "server_addr"
CONF_SERVER_PORT = "server_port"
CONF_SERVER_CERT = "server_cert"
CONF_DEBUG_LEVEL = "debug_level"
CONF_OPT_DEBUG = "opt_debug"
CONF_LOG_STDOUT = "log_stdout"

LOG_FMT = "%(asctime)s.%(msecs)d %(lineno)d %(message)s"
LOG_DATE_FMT = "%Y-%m-%dT%H:%M:%S"

app = Bottle()
logger = logging.getLogger(PROG_NAME)
handler_map = {}

@app.route("/up", method="POST")
def app_up():
    log_common(request)
    if config[CONF_DEBUG_LEVEL] > 0:
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
    '''
    kv_data is a Python object, which is seriaized of the JSON-like string
    of KEY_TOPOBJ sent by a TP NS.
    assuming that all required keys exist in the config.
    '''
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
    app_type = config[CONF_APP_TYPE].get(deveui)
    if not app_type:
        logger.error("DevEUI {} is not defined in the config.".format(deveui))
        return 403  # not found.
    '''
    call parser.parse() to try converting the payload_hex.
    if succeeded, it is set into KEY_APP_DATA.
    '''
    handler = handler_map[app_type]
    kv_payload = handler.parse(payload_hex)
    '''
    return value of parser.paser():
        None: ignore parsing.
        False: something error.
        Others: a Python dict should be put in KEY_APP_DATA.
    '''
    if kv_payload is None:
        pass
    elif kv_payload is not True:
        # if kv_payload is False variants except of None, then error.
        logger.error("Parsing payload for DevEUI {} failed.".format(deveui))
        return 400  # bad request.
    else:
        # add __app_data
        kv_data[KEY_APP_DATA] = kv_payload
    #
    handler.db_submit(kv_data)
    return 0

def log_common(request):
    logger.info("Access from {} {} {}".format(request.remote_addr,
                                              request.method, request.url))

def set_logger(config):
    #
    # set logger.
    #   "syslog", not yet
    #   "stdout"
    #   filename
    #
    log_file = config.get("log_file", "stdout")
    #
    if config[CONF_LOG_STDOUT] or log_file == "stdout":
        ch = logging.StreamHandler()
    else:
        ch = logging.FileHandler(log_file)
    #
    ch.setFormatter(logging.Formatter(fmt=LOG_FMT, datefmt=LOG_DATE_FMT))
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    if config[CONF_DEBUG_LEVEL] > 0:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

def check_config(config):
    # set PYTHONPATH
    sys.path.append("./handlers")
    for i in config.get(CONF_MODULE_PATH, []):
        sys.path.append(i)
    # check if the app_type key exists.
    app_type_map = config.get(CONF_APP_TYPE)
    if not app_type_map:
        print("ERROR: Key {} does not exist in the config."
              .format(CONF_APP_TYPE))
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
    config.setdefault(CONF_DEBUG_LEVEL, 0)
    # overwrite the debug level if opt.debug is True.
    if config[CONF_OPT_DEBUG] == True and config[CONF_DEBUG_LEVEL] == 0:
        config[CONF_DEBUG_LEVEL] = 99
    # NOTE: below check should be placed at the end of this method.
    # check if the handlers are properly defined.
    # if parser.db_submit is not defined, it will be submitted into MongoDB.
    for k,v in app_type_map.items():
        handler = handlers.get(v)
        if not handler:
            print("ERROR: the handler for {} is not defined in the config."
                  .format(k))
            return False
        mod_name = handler.get(CONF_MODULE)
        if mod_name is None:
            print("ERROR: Key {} is not defined.".format(CONF_MODULE))
            return False
        try:
            mod = import_module(mod_name)
            handler_map[v] = mod.handler(logger=logger,
                                         debug_level=config[CONF_DEBUG_LEVEL],
                                         **handler)
        except Exception as e:
            print("ERROR: import {} failed. {}".format(mod_name, e))
            return False
    return True

'''
main
'''
ap = ArgumentParser()
ap.add_argument("config_file", metavar="CONFIG_FILE",
                help="specify the config file.")
ap.add_argument("-d", action="store_true", dest="debug",
               help="enable debug mode.")
ap.add_argument("-D", action="store_true", dest="log_stdout",
               help="enable to show messages onto stdout.")
opt = ap.parse_args()
# get config.
try:
    config = json.load(open(opt.config_file))
except Exception as e:
    print("ERROR: {} read error. {}".format(opt.config_file, e))
    exit(1)
# update config.
config[CONF_OPT_DEBUG] = opt.debug
config[CONF_LOG_STDOUT] = opt.log_stdout
if not check_config(config):
    print("ERROR: error in {}.".format(opt.config_file))
    exit(1)
#
set_logger(config)
#
server_addr = config.get("server_addr")
server_port = int(config.get("server_port"))
server_cert = config.get("server_cert")
server_scheme = "https" if server_cert else "http"
logger.info("Starting {} listening on {}://{}:{}/"
            .format(PROG_NAME, server_scheme, server_addr, server_port))
#
if server_cert:
    app.run(host=server_addr, port=server_port,
            certfile=server_cert,
            server=GeventServer, quiet=True, debug=False)
else:
    app.run(host=server_addr, port=server_port,
            server=GeventServer, quiet=True, debug=False)
