# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import time
import struct
from app_util import default_logger
from parser_thru import parser

def unixtime_hexstr_to_iso8601(src):
    return time.strftime("%Y-%m-%dT%H:%M:%S+0000",
        time.gmtime(int(src, 16)))

def ieee754_hexstr_to_float(src):
    v = struct.pack(">l", int(src, 16))
    return struct.unpack(">f", v)[0]

class parser():
    '''
    hex_string: application data in hex string.
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
    @classmethod
    def parse(cls, hex_string):

        if len(hex_string) != 48:
            print("the payload length is not 48.")
            return {}

        return {
            "utc_time": unixtime_hexstr_to_iso8601(hex_string[8:16]),
            "temperature": int(hex_string[4:8],16),
            "latitude": round(ieee754_hexstr_to_float(hex_string[16:24]),6),
            "longitude": round(ieee754_hexstr_to_float(hex_string[24:32]),6),
            "altitude": round(int(hex_string[32:36],16)/10.,2),
            "speed": round(int(hex_string[36:40],16)/10.,2),
            "gyro_x": int(hex_string[40],16),
            "gyro_y": int(hex_string[42],16),
            "gyro_z": int(hex_string[44],16),
            "battery_level": int(hex_string[0:4],16)
            }

    def __init__(self, **kwargs):
        self.logger = kwargs.get("logger", default_logger)
        self.debug_level = kwargs.get("debug_level", 0)

    def submit(self, kv_data, **kwargs):
        p = parser(logger=self.logger, debug_level=self.debug_level)
        p.submit(kv_data)

'''
test code
'''
if __name__ == '__main__' :
    if len(sys.argv) == 1:
        s = "0000000058d4b41b420ea943430bbb24021d000000000000";
    else:
        s = sys.argv[1]
    print(s)
    v = parser.parse("0000000058d4b41b420ea943430bbb24021d000000000000");
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
