# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
from app_util import default_logger
from parser_thru import parser as parser_thru

class parser():

    @classmethod
    def parse(cls, hex_string):
        '''
        hex_string: application data in hex string.
        Globalsat sensor message format:
            byte: description
            1: device_type
            1: (7-6) GPS Fix Status (5-0) Report Type
            1: Battery Capacity
            4: latitude (IEEE 754)
            4: longitude (IEEE 754)
        '''
        if len(hex_string) != 22:
            print("ERROR: the payload length is not 22.")
            return {}
    
        x1 = bin(int(hex_string[2:4], 16))[2:].zfill(8)
        return {
            "device_type": int(hex_string[0:2], 16),
            "gps_fix_status": x1[:2],
            "report_type": int(x1[2:]),
            "battery_capacity": int(hex_string[4:6], 16),
            "latitude": float(int(hex_string[6:14], 16)) * 0.000001,
            "longitude": float(int(hex_string[14:22], 16)) * 0.000001
            }

    def __init__(self, **kwargs):
        self.logger = kwargs.get("logger", default_logger)
        self.debug_level = kwargs.get("debug_level", 0)

    def submit(self, kv_data, **kwargs):
        p = parser_thru(logger=self.logger, debug_level=self.debug_level)
        p.submit(kv_data)
        return True

'''
test code
'''
if __name__ == '__main__' :
    v = parser.parse("008263022034b60854231c");
    #v = parse("000261022039c508541e9b");
    print("DEBUG: ")
    print("  device_type = %s" % v["device_type"])
    print("  gps_fix_status = %s" % v["gps_fix_status"])
    print("  report_type = %s" % v["report_type"])
    print("  battery_capacity = %s %%" % v["battery_capacity"])
    print("  latitude = %s" % v["latitude"])
    print("  longitude = %s" % v["longitude"])
