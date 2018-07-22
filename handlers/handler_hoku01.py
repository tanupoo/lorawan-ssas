# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
from connector_sqlite3 import connector_sqlite3

class handler(connector_sqlite3):
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
    def parse(cls, hex_string):
    
        if len(hex_string) != 24:
            print("ERROR: the hex_string length is not 24.")
            return False
    
        h = int(hex_string[0],16)
        #
        shade_or_not = int(hex_string[1:16],16)
        s = []
        for i in range(60):
            s.append("0" if shade_or_not&1 == 0 else "1")
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

    def create_db(self, **kwargs):
        self.cur.execute("""
                         create table if not exists hoku01_data (
                            ts datetime,
                            deveui text,
                            rssi real,
                            snr real,
                            temp real,
                            humid real,
                            shaded_count number
                         )""")

    def insert_db(self, kv_data, **kwargs):
        '''
        a record inserted into a database is like below:
        xxx
        '''
        app_data = kv_data["__app_data"]
        if app_data is None:
            self.logger.error("the payload haven't been parsed.")
            return False
        app_data["ts"] = self.fix_ts(kv_data["Time"])
        app_data["deveui"] = kv_data["DevEUI"]
        app_data["rssi"] = kv_data["LrrRSSI"]
        app_data["snr"] =  kv_data["LrrSNR"]
        if self.debug_level > 0:
            self.logger.debug("app_data = {}".format(app_data))
        #
        # count the shaded.
        app_data["shaded_count"] = app_data["shaded"].count("0")
        #
        self.cur.execute("""
                         insert into hoku01_data (
                            ts, deveui, rssi, snr, temp, humid, shaded_count)
                         values (
                            :ts, :deveui, :rssi, :snr,
                            :temp, :humid, :shaded_count)
                         """, app_data)
        self.con.commit()
        if self.debug_level > 0:
            self.logger.debug("submitting app_data into sqlite3 succeeded.")
        return True

'''
test code
'''
if __name__ == '__main__' :
    v = handler.parse("0fffffffffffff3f21002300");
    #v = parse("0fffffffffffff3fa1002300");
    print("DEBUG: ")
    print("  H = %s" % v["H"])
    print("  shaded = %s" % v["shaded"])
    print("  temp = %s" % v["temp"])
    print("  humid = %s %%" % v["humid"])
