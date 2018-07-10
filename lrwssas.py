#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Shoichi Sakane <sakane@tanu.org>, All rights reserved.
# See the file LICENSE in the top level directory for more details.
#

from __future__ import print_function

import sys
import json
from datetime_timestamp import *
import logging
from datetime import datetime
from functools import wraps
from bottle import Bottle, GeventServer, request
from gevent import monkey; monkey.patch_all()
from importlib import import_module
from argparse import ArgumentParser
import requests

PROG_NAME = "lrwssas"
KEY_TOPOBJ = "DevEUI_uplink"
KEY_TIME = "Time"
KEY_PAYLOAD_HEX = "payload_hex"
KEY_DEVEUI = "DevEUI"
KEY_APP_DATA = "__app_data"

CONF_APP_TYPE = "app_type"
CONF_APP_TYPE_TRHU = "THRU"
CONF_APP_PARSER = "app_parser"
CONF_SERVER_ADDR = "server_addr"
CONF_SERVER_PORT = "server_port"
CONF_MONGODB_URL = "mongodb_url"
CONF_SERVER_CERT = "server_cert"
CONF_DEBUG_LEVEL = "debug_level"

LOG_FMT = "%(asctime)s.%(msecs)d %(lineno)d %(message)s"
LOG_DATE_FMT = "%Y-%m-%dT%H:%M:%S"

app = Bottle()
logger = logging.getLogger(PROG_NAME)
parser_mod_map = {}

@app.route("/up", method="POST")
def app_up():
    log_common(request)
    if opt.log_stdout and (opt.debug or config(CONF_DEBUG_LEVEL) > 0):
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
        jd = json.load(request.body)
    except json.decoder.JSONDecodeError as e:
        emsg = "The payload format was not likely JSON."
        logger.error("{}: {}".format(emsg, e))
        app.abort(404, emsg)
    #
    ret = proc_tp_uplink(jd)
    if ret:
        app.abort(ret)

'''
class parser():
    @classmethod
    def parse(self, payload):
        # parse the payload and return JSON,
        # which will be submitted into MongoDB.
        return {}
    @classmethod
    def submit(self, json_data):
        # submit json_data into a database such as sqlite3.
        pass
'''

def proc_tp_uplink(json_data):
    '''
    assuming that all keys exist in the config.
    '''
    # get the root object
    jd_root = json_data.get(KEY_TOPOBJ)
    if not jd_root:
        logger.error("Key {} does not exist in the request.".format(KEY_TOPOBJ))
        return 400  # bad request.
    # get deveui
    deveui = jd_root.get(KEY_DEVEUI)
    if not deveui:
        logger.error("Key {} does not exist in the request.".format(KEY_DEVEUI))
        return 400  # bad request.
    # get payload_hex
    payload_hex = jd_root.get(KEY_PAYLOAD_HEX)
    if not payload_hex:
        logger.error("Key {} does not exist in the request."
                     .format(KEY_PAYLOAD_HEX))
        return 400  # bad request.
    # get time, for processing later.
    jd_time = jd_root.get(KEY_TIME)
    if not jd_time:
        logger.error("key {} does not exist in the request.".format(KEY_TIME))
        return 400  # bad request.
    #
    logger.info("Received data from {}".format(deveui))
    # get the parser.
    app_type = config[CONF_APP_TYPE].get(deveui)
    if not app_type:
        logger.error("DevEUI {} is not defined in the config.".format(deveui))
        return 403  # not found.
    '''
    if app_type is CONF_APP_TYPE_TRHU, the payload will not be converted,
    then submit it into MonghDB.
    in other case, try to parse the payload and convert into the JSON string,
    try to call app_parser.submit(), if it doesn't exist. submit it into the
    MongoDB.
    '''
    if app_type == CONF_APP_TYPE_TRHU:
        submit_mongodb(json_data)
    else:
        app_parser = config[CONF_APP_PARSER].get(app_type)
        parser = parser_mod_map[app_parser]
        jd_payload = parser.parse(payload_hex, logger=logger)
        if not jd_payload:
            logger.error("Parsing payload for DevEUI {} failed.".format(deveui))
            return 400  # bad request.
        # add __app_data
        json_data[KEY_TOPOBJ][KEY_APP_DATA] = jd_payload
        # submit json_data
        try:
            parser.submit(json_data)
        except AttributeError:
            submit_mongodb(json_data)
    #
    return 0

def submit_mongodb(json_data):
    '''
    if CONF_MONGODB_URL is not defined in the config, do nothing.
    otherwise,
    convert ISO8601 time into JSON object for MongoDB.
    submit json data into MongoDB via REST API.
    assuming that all keys are exist in the json data.
    because it assumes that proc_tp_uplink() has been called already.
    '''
    db_url = config.get(CONF_MONGODB_URL)
    if not db_url:
        return
    # get the root object
    jd_root = json_data.get(KEY_TOPOBJ)
    # get datetime
    jd_time = jd_root[KEY_TIME]
    # Convert ISO8601 format in DevEUI_uplink.Time of JSON into MongoDB date.
    json_data[KEY_TOPOBJ][KEY_TIME] = json.loads('{{"$date":{}}}'
                                    .format(iso8601_to_timestamp_ms(jd_time)))
    # submit.
    print(json_data)
    print(config[CONF_MONGODB_URL])
    ret = requests.post(config[CONF_MONGODB_URL], data=json.dumps(json_data))
    if ret.ok:
        ret_value = ret.json()
        if ret_value == '{ "ok" : true }':
            if opt.debug or config.get(CONF_DEBUG_LEVEL) > 0:
                logger.debug("Submitting data into MongoDB succeeded.")
        else:
            logger.error("MongoDB's response: {}".format(ret_value))
    else:
        logger.error("Submitting data into MongoDB failed. {} {} {}"
            .format(ret.status_code, ret.reason, ret.text))


def log_common(request):
    request_time = datetime.now()
    logger.info("Access from {} {} {}".format(request.remote_addr,
                                              request.method, request.url))

def set_logger(config, opt):
    #
    # set logger.
    #   "syslog", not yet
    #   "stdout"
    #   filename
    #
    log_file = config.get("log_file", "stdout")
    #
    if opt.log_stdout or log_file == "stdout":
        ch = logging.StreamHandler()
    else:
        ch = logging.FileHandler(log_file)
    #
    ch.setFormatter(logging.Formatter(fmt=LOG_FMT, datefmt=LOG_DATE_FMT))
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    if opt.debug or config.get(CONF_DEBUG_LEVEL) > 0:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

def check_config(config):
    # check if the app_type key exists.
    app_type_map = config.get(CONF_APP_TYPE)
    if not app_type_map:
        print("Key {} does not exist in the config.".format(CONF_APP_TYPE))
        return False
    # check if the app_parser key exists.
    app_parser_map = config.get(CONF_APP_PARSER)
    if not app_parser_map:
        print("Key {} does not exist in the config.".format(CONF_PARSER_TYPE))
        return False
    # check if the parser is defined.
    # if app_type is CONF_APP_TYPE_TRHU, it's out of scope.
    # if parser.submit is not defined, it will be submitted into MongoDB.
    '''
    if "" not in sys.path:
        sys.path.append("")
        print("zero length string was added into sys.path.")
    '''
    for k,v in app_type_map.items():
        if v == CONF_APP_TYPE_TRHU:
            continue
        app_parser = app_parser_map.get(v)
        if not app_parser:
            print("Parser for {} is not defined in the config.".format(k))
            return False
        mod = import_module(app_parser)
        parser = mod.parser()
        if not getattr(parser, "parse"):
            print("parse() is not defined in the parser module for {}."
                         .format(k))
            return False
        parser_mod_map[app_parser] = parser
    #
    if not config.setdefault(CONF_MONGODB_URL, None):
        print("""NOTICE: URL of MongoDB is not defined. \
Any data will not be stored unless you define submit() \
in your parser.""")
    config.setdefault(CONF_SERVER_ADDR, "::")
    config.setdefault(CONF_SERVER_PORT, "18886")
    config.setdefault(CONF_SERVER_CERT, None)
    config.setdefault(CONF_DEBUG_LEVEL, 0)
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
if not check_config(config):
    print("ERROR: config error.")
    exit(1)
#
set_logger(config, opt)
#
server_addr = config.get("server_addr")
server_port = int(config.get("server_port"))
server_cert = config.get("server_cert")
server_scheme = "https" if server_cert else "http"
logger.info("Starting {} listening on {}://{}:{}/"
            .format(PROG_NAME, server_scheme, server_addr, server_port))
#
app.run(host=server_addr, port=server_port,
        server=GeventServer, quiet=True, debug=False,
        certfile=server_cert)
