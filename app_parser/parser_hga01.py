#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import time
import struct

def hexstr_unixtime_to_iso8601(src):
    return time.strftime("%Y-%m-%dT%H:%M:%S+0000",
        time.gmtime(int(src, 16)))

def hexstr_ieee754_to_float(src):
    v = struct.pack(">l", int(src, 16))
    return struct.unpack(">f", v)[0]

'''
payload: application data in hex string.
HGA sensor message format:
    byte: description
    2: battery level (0~254, 0: external powered) mV?
    2: temperature
    4: utc time
    4: latitude (IEEE 754)
    4: longitude (IEEE 754)
    2: altitude (unit: 0.1 m)
    2: speed (unit: 0.1 km/h)
    1: gyro x (-4 ~ +4)
    1: gyro y (-4 ~ +4)
    1: gyro z (-4 ~ +4)
    1: RFU
'''
def parse(payload):

    if len(payload) != 48:
        print("ERROR: the payload length is not 48.")
        return {}

    return {
        "utc_time": hexstr_unixtime_to_iso8601(payload[8:16]),
        "temperature": "%d" % int(payload[4:8], 16),
        "latitude": "%.6f" % hexstr_ieee754_to_float(payload[16:24]),
        "longitude": "%.6f" % hexstr_ieee754_to_float(payload[24:32]),
        "altitude": "%.2f" % float(int(payload[32:36], 16) / 10),
        "speed": "%.2f" % float(int(payload[36:40], 16) / 10),
        "gyro_x": "%d" % int(payload[40], 16),
        "gyro_y": "%d" % int(payload[42], 16),
        "gyro_z": "%d" % int(payload[44], 16),
        "battery_level": "%d" % int(payload[0:4], 16)
        }

'''
test code
'''
if __name__ == '__main__' :
    v = parse("0000000058d4b41b420ea943430bbb24021d000000000000");
    print("DEBUG: ")
    print("  utc_time = %s" % v["utc_time"])
    print("  temperature = %s ?" % v["temperature"])
    print("  latitude = %s" % v["latitude"])
    print("  longitude = %s" % v["longitude"])
    print("  altitude = %s m" % v["altitude"])
    print("  speed = %s km/h" % v["speed"])
    print("  gyro_x = %s" % v["gyro_x"])
    print("  gyro_y = %s" % v["gyro_y"])
    print("  gyro_z = %s" % v["gyro_z"])
    print("  battery level = %s ?" % v["battery_level"])
