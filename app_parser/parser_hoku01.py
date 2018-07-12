# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
from app_util import default_logger

class parser():
    '''
    hex_string: application data in hex string.
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
    @classmethod
    def parse(cls, hex_string, logger=default_logger):
    
        if len(hex_string) != 24:
            print("ERROR: the hex_string length is not 24.")
            return {}
    
        h = int(hex_string[0],16)
        #
        shade_or_not = int(hex_string[1:16],16)
        s = []
        for i in range(60):
            s.append("1" if shade_or_not&1 == 0 else "0")
            shade_or_not >>= 1
        shaded = "".join(reversed(s))
        #
        temp_sign = 1 if int(hex_string[16],16)&0x8 == 0 else -1
        temp = (int(hex_string[16:18],16)&0x7f) + int(hex_string[18:20],16)/100
        temp *= temp_sign
        #
        humid = int(hex_string[20:22],16) + int(hex_string[22:24],16)/100
        #
        return {
            "H": h,
            "shaded": shaded,
            "temp": float(temp),
            "humid": float(humid)
            }

    def __init__(self, **kwargs):
        # e.g. open a session to a database.
        # kwargs should contain: logger, debug_level
        self.logger = kwargs.get("logger", default_logger)
        self.debug_level = kwargs.get("debug_level", 0)

    def submit(self, kv_data, **kwargs):
        '''
        - submit the data into a database such as mongodb or sqlite3.
        '''
        pass

'''
test code
'''
if __name__ == '__main__' :
    v = parser.parse("0fffffffffffff3f21002300");
    #v = parse("0fffffffffffff3fa1002300");
    print("DEBUG: ")
    print("  H = %s" % v["H"])
    print("  shaded = %s" % v["shaded"])
    print("  temp = %s" % v["temp"])
    print("  humid = %s %%" % v["humid"])
