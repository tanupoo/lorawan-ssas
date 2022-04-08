#!/usr/bin/env python

import json
from datetime import datetime
import time
import random
import requests

# XXX lon,lat in payload_hex should be variable.
src_data = {
    "DevEUI": "0102030405060708",
    "DevAddr": "AA000011",
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

from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter
ap = ArgumentParser(
        description="pseudo NS message submitter for test.",
        formatter_class=ArgumentDefaultsHelpFormatter)
ap.add_argument("url", help="url for submission.")
ap.add_argument("--deveui", action="store", dest="deveui",
                help="DevEUI of the device")
ap.add_argument("--devaddr", action="store", dest="devaddr",
                help="DevAddr of the device")
ap.add_argument("-i", action="store", dest="interval", type=int, default=60,
                help="interval to submit the message.")
ap.add_argument("-n", action="store", dest="nb_loop", type=int, default=None,
                help="specify the number of times to submit.")
ap.add_argument("-k", action="store_false", dest="tls_verify",
                help="disable to verify the server certificate.")
ap.add_argument("-d", action="store_true", dest="debug",
                help="enable debug mode.")
opt = ap.parse_args()

#
# main
#
headers = {}
headers["Content-Type"] = "application/json"

if opt.deveui is not None:
    src_data["DevEUI"] = opt.deveui
if opt.devaddr is not None:
    src_data["DevAddr"] = opt.devaddr

while True:
    # update time
    src_data["Time"] = datetime.now().isoformat()[:-3] + "+09:00"
    # produce the complete message.
    message = {}
    message.update({"DevEUI_uplink": src_data})
    payload = json.dumps(message)
    if opt.debug:
        print(message)
    # update the header.
    headers["Content-Length"] = str(len(payload))
    #
    ret = requests.post(opt.url, headers=headers, data=payload,
                        verify=opt.tls_verify)
    #
    if opt.nb_loop is None:
        break
    elif opt.nb_loop > 0:
        opt.nb_loop -= 1
        if opt.nb_loop == 0:
            break
        else:
            pass
    # opt.nb_loop is 0 passed by the option.
    time.sleep(opt.interval)
    continue

