# -*- coding: utf-8 -*-

from __future__ import print_function

import sys

from binascii import a2b_hex
from struct import unpack
from app_util import default_logger

# the specification are in the following document.
# https://www.yokogawa.co.jp/solutions/solutions/iiot/maintenance/sushi-sensor-j/#%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88%EF%BC%86%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89

# it is to ignore import error for just parsing the payload.
try:
    import sqlite3
except:
    pass

def parse_x10(data):
    '''
    0x10 Z
    0x11 XYZ
    10 0000 39e1 354a 4f10
    b'\x00\x00',-668.5,12.4140625,0.0005259513854980469
    '''
    return {
        "status": data[1:3],
        "accel": unpack(">e",data[3:5])[0],
        "velocity": unpack(">e",data[5:7])[0],
        "temp": unpack(">e",data[7:9])[0] }

def parse_x12(data):
    '''
    0x12 X
    0x13 Y
    '''
    return {
        "status": data[1:3],
        "accel": unpack(">e",data[3:5])[0],
        "velocity": unpack(">e",data[5:7])[0] }

def parse_x40(data):
    return {
        "uptime": unpack(">I",b"\x00"+data[1:4])[0],
        "battery": data[4]/2,
        "rssi": -1*data[5],
        "per": data[6],
        "snr": data[7]/4 }

def parse_x41(data):
    return {
        "status": "".join(["{:02x}".format(i) for i in data[1:5]]),
        "detail": "".join(["{:02x}".format(i) for i in data[5:9]]) }

def parse_x42(data):
    return {
        "tag": data[1:11] }

def parse_x43(data):
    return {
        "lon": unpack(">f",data[1:5])[0],
        "lat": unpack(">f",data[5:9])[0] }

data_tab = [
    { "data_type":0x10, "parser":parse_x10 },
    { "data_type":0x11, "parser":parse_x10 },
    { "data_type":0x12, "parser":parse_x12 },
    { "data_type":0x13, "parser":parse_x12 },
    { "data_type":0x40, "parser":parse_x40 },
    { "data_type":0x41, "parser":parse_x41 },
    { "data_type":0x42, "parser":parse_x42 },
    { "data_type":0x43, "parser":parse_x43 },
    ]

class parser():

    @classmethod
    def parse(cls, hex_string):
    
        def parse_data_type(data):
            for t in data_tab:
                if data[0] == t["data_type"]:
                    d = t["parser"](data)
                    d["data_type"] = data[0]
                    return d
            print("ERROR: unknown data type {:02x}".format(data[0]))
            return False
    
        # check whether it should be ignored.
        # this is to compare a string of "None", not the None object.
        if hex_string == "None":
            return None
    
        return parse_data_type(a2b_hex(hex_string))

    '''
    {'status': b'\x00\x00', 'accel': 0.75830078125, 'velocity': 0.302734375,
    'temp': 33.25, 'data_type': 16, 'Time': '2017-03-24T06:53:32.502+01:00'}
    '''
    def __init__(self, **kwargs):
        self.logger = kwargs.get("logger", default_logger)
        self.debug_level = kwargs.get("debug_level", 0)
        self.con = sqlite3.connect("xs770a.db")
        self.cur = self.con.cursor()
        if self.cur is not None:
            self.cur.execute("""\
create table if not exists app_data \
    (ts, rssi, snr, accel, velocity, temp)""")

    def submit(self, kv_data, **kwargs):
        app_data = kv_data["DevEUI_uplink"]["__app_data"]
        if app_data["data_type"] not in [0x10, 0x11]:
            return None
        app_data["ts"] = kv_data["DevEUI_uplink"]["Time"]
        app_data["rssi"] = kv_data["DevEUI_uplink"]["LrrRSSI"]
        app_data["snr"] =  kv_data["DevEUI_uplink"]["LrrSNR"]
        #
        if self.debug_level > 0:
            self.logger.debug("app_data =", app_data)
        #
        self.cur.execute("""\
insert into app_data(ts, rssi, snr, accel, velocity, temp) \
    values (:ts, :rssi, :snr, :accel, :velocity, :temp)""",
            app_data)
        self.con.commit()
        #
        if self.debug_level > 0:
            self.logger.debug("submitting app_data into sqlite3 succeeded.")
        return True

'''
test code
'''
if __name__ == '__main__' :
    if len(sys.argv) == 1:
        s = "1000003a1134d85028";
    else:
        s = sys.argv[1]
    print(s)
    v = parser.parse("1000003a1134d85028");
    print("DEBUG:")
    for k,v in v.items():
        print("  {} = {}".format(k,v))
