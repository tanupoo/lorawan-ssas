# -*- coding: utf-8 -*-

from __future__ import print_function

import sys

class parser():
    '''
    payload: application data in hex string.
    Globalsat sensor message format:
        byte: description
        1: device_type
        1: (7-6) GPS Fix Status (5-0) Report Type
        1: Battery Capacity
        4: latitude (IEEE 754)
        4: longitude (IEEE 754)
    '''
    @classmethod
    def parse(cls, payload):
    
        if len(payload) != 22:
            print("ERROR: the payload length is not 22.")
            return {}
    
        x1 = bin(int(payload[2:4], 16))[2:].zfill(8)
        return {
            "device_type": "%d" % int(payload[0:2], 16),
            "gps_fix_status": "%s" % x1[:2],
            "report_type": "%d" % int(x1[2:]),
            "battery_capacity": "%d" % int(payload[4:6], 16),
            "latitude": "%.6f" % (float(int(payload[6:14], 16)) * 0.000001),
            "longitude": "%.6f" % (float(int(payload[14:22], 16)) * 0.000001)
            }

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
