#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

'''
see sample.json
'''

import sys
import json
from datetime import datetime
import time
import random
import httplib2
import argparse

# XXX lon,lat in payload_hex should be variable.
ns_fixed = {
    "payload_hex" : "0000000058d4b41b420ea943430bbb24021d000000000000",
    "Lrcid" : "00000201",
    "Lrrid" : "69606FD0",
    "LrrLAT" : "35.665005",
    "LrrRSSI" : "0.000000",
    "LrrSNR" : "-20.000000",
    "LrrLON" : "139.731293",
    "DevLrrCnt" : "1",
    "Lrrs" : {
        "Lrr" : {
        "LrrESP" : "-20.043213",
        "LrrSNR" : "-20.000000",
        "Lrrid" : "69606FD0",
        "Chain" : "0",
        "LrrRSSI" : "0.000000"
        }
    },
    "CustomerID" : "100000778",
    "CustomerData" : {
        "alr" : {
        "pro" : "ADRF/DEMO",
        "ver" : "1"
        }
    },
    "FCntUp" : "7970",
    "Channel" : "LC5",
    "SubBand" : "G0",
    "ModelCfg" : "0",
    "Late" : "0",
    "ADRbit" : "1",
    "FCntDn" : "2",
    "SpFact" : "12",
    "MType" : "4",
    "FPort" : "2",
    "mic_hex" : "6fa15f9f",
    }

def parse_args():
    p = argparse.ArgumentParser(
            description="This is a pseudo NS message generator.")
    p.add_argument("server", metavar="URL", type=str,
        help="url of the server")
    p.add_argument("deveui", metavar="DevEUI", type=str,
        help="DevEUI of the device")
    p.add_argument("devaddr", metavar="DevAddr", type=str,
        help="DevAddr of the device")
    p.add_argument("-i", action="store", dest="interval", type=int, default=30,
                   help="interval to send the message.")
    p.add_argument("-d", action="append_const", dest="_f_debug",
                   default=[], const=1, help="increase debug mode.")
    p.add_argument("--debug", action="store", dest="_debug_level", default=0,
        help="specify a debug level.")

    args = p.parse_args()
    if len(args._f_debug) and args._debug_level != -1:
        print("ERROR: use either -d or --debug option.")
        exit(1)
    if args._debug_level == -1:
        args._debug_level = 0
    args.debug_level = len(args._f_debug) + args._debug_level

    return args

#
# main
#
opt = parse_args()
http = httplib2.Http(timeout=5)
headers = {}
headers["Content-Type"] = "application/json"

ns_data = {}
while True:
    ns_fixed["DevEUI"] = opt.deveui
    ns_fixed["DevAddr"] = opt.devaddr
    ns_fixed["Time"] = datetime.now().isoformat()[:-3] + "+09:00"
    ns_data["DevEUI_uplink"] = ns_fixed
    payload = json.dumps(ns_data)
    headers["Content-Length"] = str(len(payload))
    res_headers, res_body = http.request(opt.server, method="POST",
            body=payload, headers=headers)
    time.sleep(30)

