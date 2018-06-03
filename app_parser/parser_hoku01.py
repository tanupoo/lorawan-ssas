# -*- coding: utf-8 -*-

from __future__ import print_function

import sys

'''
payload: application data in hex string.
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |   H   |                                                       |
    +-+-+-+-+-+-+-+-+-+-+-+-+  Shade or Not  -+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |          Temperature          |           Humidity            |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

     0                   1           
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |S|   Integer   |    Decimal    |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
'''
def parse(payload):

    if len(payload) != 24:
        print("ERROR: the payload length is not 24.")
        return {}

    h = int(payload[0],16)
    #
    shade_or_not = int(payload[1:16],16)
    s = []
    for i in range(60):
        s.append("1" if shade_or_not&1 == 0 else "0")
        shade_or_not >>= 1
    shaded = "".join(reversed(s))
    #
    temp_sign = 1 if int(payload[16],16)&0x8 == 0 else -1
    temp = (int(payload[16:18],16)&0x7f) + int(payload[18:20],16)/100
    temp *= temp_sign
    #
    humid = int(payload[20:22],16) + int(payload[22:24],16)/100
    #
    return {
        "H": "%d" % h,
        "shaded": "%s" % shaded,
        "temp": "%.2f" % temp,
        "humid": "%.2f" % humid
        }

'''
test code
'''
if __name__ == '__main__' :
    v = parse("0fffffffffffff3f21002300");
    #v = parse("0fffffffffffff3fa1002300");
    print("DEBUG: ")
    print("  H = %s" % v["H"])
    print("  shaded = %s" % v["shaded"])
    print("  temp = %s" % v["temp"])
    print("  humid = %s %%" % v["humid"])
