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
        "temperature": int(payload[4:8], 16),
        "latitude": hexstr_ieee754_to_float(payload[16:24]),
        "longitude": hexstr_ieee754_to_float(payload[24:32]),
        "altitude": float(int(payload[32:36], 16) / 10),
        "speed": float(int(payload[36:40], 16) / 10),
        "gyro_x": int(payload[40], 16),
        "gyro_y": int(payload[42], 16),
        "gyro_z": int(payload[44], 16),
        "battery_level": int(payload[0:4], 16)
        }

'''
test code
'''
if __name__ == '__main__' :
    v = appHga("0000000058d4b41b420ea943430bbb24021d000000000000");
    print("DEBUG: ")
    print("  utc_time = %s" % v["utc_time"])
    print("  temperature = %d ?" % v["temperature"])
    print("  latitude = %f" % v["latitude"])
    print("  longitude = %f" % v["longitude"])
    print("  altitude = %.1f m" % v["altitude"])
    print("  speed = %.1f km/h" % v["speed"])
    print("  gyro_x = %d" % v["gyro_x"])
    print("  gyro_y = %d" % v["gyro_y"])
    print("  gyro_z = %d" % v["gyro_z"])
    print("  battery level = %d ?" % v["battery_level"])
