#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Shoichi Sakane <sakane@tanu.org>, All rights reserved.
# See the file LICENSE in the top level directory for more details.
#

from __future__ import print_function

import sys
import json
import re
import httplib2
from tiny_http_server import *
from app_parser import *
from datetime_timestamp import *

KEY_TOPOBJ = "DevEUI_uplink"
KEY_TIME = "Time"
KEY_PAYLOAD_HEX = "payload_hex"
KEY_DEVEUI = "DevEUI"
KEY_APP_DATA = "__app_data"
CONF_APP_MAP = "app_map"
CONF_SERV_PATH = "server_path"
CONF_DB_URL = "db_url"
DEVTYPE_HGA_HGOK_IOT_SN13 = "HGA_HGOK_IoT_SN13"
DEVTYPE_GLOBALSAT_TL_100 = "GLOBALSAT_TL_100"
MONGODB_DEFUALT_TIMEOUT = 3

import sys

'''
'''
class LoRawanSuperSimpleASHandler(ChunkableHTTPRequestHandler):

    __version__ = '0.1'

    def do_GET(self):
        pass

    def post_read(self, payload):
        #server_path = self.server.config.get("server_path", "")
        #if server_path and self.path[:len(server_path)] != server_path:
        #    raise ValueError(
        #            "ERROR: accessing to %s is not allowed, should be %s" %
        #            (self.path, server_path))
        # XXX should check the path.
        self.logger.log(DEBUG3, '---BEGIN OF REQUESTED DATA---')
        self.logger.log(DEBUG3, payload)
        self.logger.log(DEBUG3, '---END OF REQUESTED DATA---')
        msg = self.convert_payload(payload, config=self.server.config)
        if not msg:
            raise RuntimeError("ERROR: payload conversion has failed.")
        res = self.http_post(self.server.config[CONF_DB_URL], msg,
                        ctype="application/json", config=self.server.config)
        if res != '{ "ok" : true }':
            self.logger.error("MongoDB's response: %s" % repr(res))
        self.put_response("OK")

    def put_response(self, contents, ctype='text/html'):
        msg_list = []
        if contents:
            msg_list.extend(contents)
        size = reduce(lambda a, b: a + len(b), msg_list, 0)
        self.send_once(msg_list, size, ctype=ctype)

    '''
    Send POST request with the payload to the URL specified.
    '''
    def http_post(self, url, payload, ctype="text/plain", config=None):
        headers = {}
        headers["Content-Type"] = ctype
        headers["Content-Length"] = str(len(payload))
        http = httplib2.Http(timeout=config.get("timeout", MONGODB_DEFUALT_TIMEOUT))
        try:
            res_headers, res_body = http.request(url, method="POST",
                    body=payload, headers=headers)
        except Exception as e:
            if len(e.message) == 0:
                self.logger.error("protocol for mongodb is not correct.")
            else:
                self.logger.error(e)
            return None
        self.logger.debug("HTTP: %s %s" % (res_headers.status, res_headers.reason))
        self.logger.log(DEBUG2, "=== BEGIN: response headers")
        self.logger.log(DEBUG2, "\n%s" % "".join(
                [ "%s: %s\n" % (k, v) for k, v in res_headers.iteritems()]))
        self.logger.log(DEBUG2, "=== END: response headers")
        return res_body

    '''
    convert the JSON string in the payload into the JSON string for the database.
    if there is no entry specifying the application for the payload,
    the part of the application payload will not be changed.
    '''
    def convert_payload(self, payload, config=None):
        try:
            jd = json.loads(payload)
        except Exception as e:
            self.logger.error("convert_payload: %s" % repr(e))
            return None
        jd = self.convert_app_payload(jd, config=config)
        jd = self.convert_app_time(jd, config=config)
        return json.dumps(jd)

    '''
    Convert ISO8601 format in DevEUI_uplink.Time of JSON into MongoDB date.
    Return JSON, or return None if in error.
    '''
    def convert_json_timestamp(self, dt_str):
        return json.loads('{ "$date" : %d }' % iso8601_to_timestamp_ms(dt_str))

    def convert_json_datetime(self, dt_str):
        # remove a colon in TZ if exists.
        re_canon = re.compile(r"\+(\d+):(\d+)")
        return json.loads(mongo_time_value % re_canon.sub(r"+\1\2", dt_str))

    def convert_app_time(self, json_data, config=None):
        mongo_time_value = '{ "$date" : "%s" }'
        # get the root object
        j = json_data.get(KEY_TOPOBJ)
        if not j:
            self.logger.error("key %s doesn't exist in the payload." % KEY_TOPOBJ)
            return None
        # get datetime
        j = j[KEY_TIME]
        if not j:
            self.logger.error("key %s doesn't exist in the payload." % KEY_TIME)
            return None
        self.logger.log(DEBUG2, "%s.%s = %s" % (KEY_TOPOBJ, KEY_TIME, j))
        json_data[KEY_TOPOBJ][KEY_TIME] = self.convert_json_timestamp(j)
        return json_data

    '''
    Convert the hex string of the application payload
    in DevEUI_uplink.payload_hex into the application JSON data
    coresponding to the application type.
    Return JSON, or return None if in error.
    '''
    def convert_app_payload(self, json_data, config=None):
        appmap = config[CONF_APP_MAP]
        if not len(appmap):
            return json_data
        # get the root object
        j_root = json_data.get(KEY_TOPOBJ)
        if not j_root:
            self.logger.error("key %s doesn't exist in the payload." % KEY_TOPOBJ)
            return None
        # get payload_hex
        hex_pl = j_root.get(KEY_PAYLOAD_HEX)
        if not hex_pl:
            self.logger.error("key %s doesn't exist in the payload." % KEY_PAYLOAD_HEX)
            return None
        self.logger.log(DEBUG2, "%s.%s = %s" % (KEY_TOPOBJ, KEY_PAYLOAD_HEX, hex_pl))
        # get deveui
        deveui = j_root.get(KEY_DEVEUI)
        if not deveui:
            self.logger.error("key %s doesn't exist in the payload." % KEY_DEVEUI)
            return None
        self.logger.log(DEBUG2, "%s.%s = %s" % (KEY_TOPOBJ, KEY_DEVEUI, deveui))
        # convert the payload
        devtype = appmap.get(deveui)
        if devtype == DEVTYPE_HGA_HGOK_IOT_SN13:
            j = parser_hga01.parse(hex_pl)
        elif devtype == DEVTYPE_GLOBALSAT_TL_100:
            j = parser_gs01.parse(hex_pl)
        else:
            # return the data as it is.
            return json_data
        json_data[KEY_TOPOBJ][KEY_APP_DATA] = j
        return json_data

'''
main
'''
httpd = TinyHTTPServer(LoRawanSuperSimpleASHandler, appname="lrwssas")
httpd.set_config()
httpd.set_opt(CONF_DB_URL)
httpd.set_opt(CONF_SERV_PATH, required=False)
httpd.set_opt(CONF_APP_MAP, type=dict, default=None, required=False)
# check the app_map
if not httpd.config[CONF_APP_MAP]:
    print("INFO: %s is not defined in the config." % CONF_APP_MAP)
httpd.run()

