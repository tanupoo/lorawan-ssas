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

'''
Send POST request with the payload to the URL specified.
'''
def http_post(url, payload, ctype="text/plain", config=None):
    headers = {}
    headers["Content-Type"] = ctype
    headers["Content-Length"] = str(len(payload))
    http = httplib2.Http(timeout=config.get("timeout", MONGODB_DEFUALT_TIMEOUT))
    try:
        res_headers, res_body = http.request(url, method="POST",
                body=payload, headers=headers)
    except Exception as e:
        if len(e.message) == 0:
            print("ERROR: protocol for mongodb is not correct.")
        else:
            print("ERROR: ", e)
        return None
    if config.get("debug_level", 0) >= 1:
        print("DEBUG: HTTP: %s %s" % (res_headers.status, res_headers.reason))
    if config.get("debug_level", 0) >= 2:
        print("DEBUG: === BEGIN: response headers")
        for k, v in res_headers.iteritems():
            print("DEBUG: %s: %s" % (k, v))
        print("DEBUG: === END: response headers")
    return res_body

'''
Convert ISO8601 format in DevEUI_uplink.Time of JSON into MongoDB date.
Return JSON, or return None if in error.
'''
def convert_json_timestamp(json_data, config=None):
    mongo_time_value = '{ "$date" : "%s" }'
    # get the root object
    j = json_data.get(KEY_TOPOBJ)
    if not j:
        print("ERROR: key %s doesn't exist in the payload." % KEY_TOPOBJ)
        return None
    # get datetime
    j = j[KEY_TIME]
    if not j:
        print("ERROR: key %s doesn't exist in the payload." % KEY_TIME)
        return None
    if config.get("debug_level", 0) >= 2:
        print("DEBUG: %s.%s = %s" % (KEY_TOPOBJ, KEY_TIME, j))
    # remove a colon in TZ if exists.
    re_canon = re.compile(r"\+(\d+):(\d+)")
    json_data[KEY_TOPOBJ][KEY_TIME] = json.loads(mongo_time_value %
                                          re_canon.sub(r"+\1\2", j))
    return json_data

'''
Convert the hex string of the application payload in DevEUI_uplink.payload_hex
into the application JSON data coresponding to the application type.
Return JSON, or return None if in error.
'''
def convert_app_payload(json_data, config=None):
    appmap = config[CONF_APP_MAP]
    if not len(appmap):
        return json_data
    # get the root object
    j_root = json_data.get(KEY_TOPOBJ)
    if not j_root:
        print("ERROR: key %s doesn't exist in the payload." % KEY_TOPOBJ)
        return None
    # get payload_hex
    hex_pl = j_root.get(KEY_PAYLOAD_HEX)
    if not hex_pl:
        print("ERROR: key %s doesn't exist in the payload." % KEY_PAYLOAD_HEX)
        return None
    if config.get("debug_level", 0) >= 2:
        print("DEBUG: %s.%s = %s" % (KEY_TOPOBJ, KEY_PAYLOAD_HEX, hex_pl))
    # get deveui
    deveui = j_root.get(KEY_DEVEUI)
    if not deveui:
        print("ERROR: key %s doesn't exist in the payload." % KEY_DEVEUI)
        return None
    if config.get("debug_level", 0) >= 2:
        print("DEBUG: %s.%s = %s" % (KEY_TOPOBJ, KEY_DEVEUI, deveui))
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
convert the JSON string in the payload into the JSON string for the database.
if there is no entry specifying the application for the payload,
the part of the application payload will not be changed.
'''
def convert_payload(payload, config=None):
    try:
        jd = json.loads(payload)
    except Exception as e:
        print("ERROR: convert_payload: ", e)
        return None
    jd = convert_app_payload(jd, config=config)
    jd = convert_json_timestamp(jd, config=config)
    return json.dumps(jd)

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
        if self._is_debug(3):
            print('---BEGIN OF REQUESTED DATA---')
            print(payload)
            print('---END OF REQUESTED DATA---')
        msg = convert_payload(payload, config=self.server.config)
        if not msg:
            raise RuntimeError("ERROR: payload conversion has failed.")
        res = http_post(self.server.config[CONF_DB_URL], msg,
                        ctype="application/json", config=self.server.config)
        if res:
            if self.server.config.get("debug_level", 0) >= 2:
                print("DEBUG: MongoDB's response: ", res)
        self.put_response("OK")

'''
test
'''
if __name__ == '__main__':
    httpd = TinyHTTPServer(LoRawanSuperSimpleASHandler)
    httpd.set_config()
    httpd.set_opt(CONF_DB_URL)
    httpd.set_opt(CONF_SERV_PATH, required=False)
    httpd.set_opt(CONF_APP_MAP, type=dict, default=None, required=False)
    # check the app_map
    if not httpd.config[CONF_APP_MAP]:
        print("INFO: %s is not defined in the config." % CONF_APP_MAP)
    httpd.run()

