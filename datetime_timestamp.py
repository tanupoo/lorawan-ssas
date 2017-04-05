#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from datetime import datetime, timedelta
import dateutil.tz
import dateutil.parser

__tz_gmt = dateutil.tz.gettz("GMT")
__epoch = datetime(1970, 1, 1, tzinfo=__tz_gmt)

def naive_to_aware(dt, tzinfo=__tz_gmt):
    if dt.tzinfo == None or dt.tzinfo.utcoffset(dt) == None:
        return dt.replace(tzinfo=tzinfo)
    return dt

def datetime_to_timestamp(dt, tzinfo=__tz_gmt):
    dt_aware = naive_to_aware(dt, tzinfo=tzinfo)
    return int((dt_aware.astimezone(tzinfo) - __epoch).total_seconds())

def iso8601_to_timestamp(s, tzinfo=__tz_gmt):
    dt = dateutil.parser.parse(s)
    return datetime_to_timestamp(dt, tzinfo=tzinfo)

def iso8601_to_timestamp_ms(s, tzinfo=__tz_gmt):
    ts = 1000 * iso8601_to_timestamp(s, tzinfo=tzinfo)
    if "." in s:
        ms = s[1+s.find("."):]
        if "+" in ms:
            ms = ms[:ms.find("+")]
        return ts + int(ms[:3].ljust(3,"0"))
    return ts

if __name__ == '__main__':
    # 2017-04-05T14:27:57.944+02:00 => 1491395277944
    print(iso8601_to_timestamp_ms("2017-04-05T14:27:57.944+02:00"))
    #print(iso8601_to_timestamp_ms("2017-03-24T06:53:32.502+01:00"))
    #print(iso8601_to_timestamp_ms("2017-03-24T06:53:32.50+01:00"))
    #print(iso8601_to_timestamp_ms("2017-03-24T06:53:32.50"))
    #print(iso8601_to_timestamp_ms("2017-03-24T06:53:32.502345"))
    #print(iso8601_to_timestamp_ms("2017-03-24T06:53:32"))

'''
from datetime_timestamp import *
'''

