class default_logger():

    @classmethod
    def critical(cls, s):
        print("CRITICAL:", s)

    @classmethod
    def error(cls, s):
        print("ERROR:", s)

    @classmethod
    def warning(cls, s):
        print("WARNING:", s)

    @classmethod
    def info(cls, s):
        print("INFO:", s)

    @classmethod
    def debug(cls, s):
        print("DEBUG:", s)

from datetime import datetime
import dateutil.tz
import dateutil.parser

def iso8601_to_ms(s, tz="GMT"):
    """
    adding milliseconds into the time string.
    tz is a default timezone. If the string looks a naive dateime string,
    it is converted into the aware datetime object with the tz string.
    """
    default_tzinfo = dateutil.tz.gettz(tz)
    # convert the string into a datetime object.
    dt = dateutil.parser.parse(s)
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) == None:
        # if naive, or if the UTC offset isn't known,
        # convert it into the aware datetime object.
        dt = dt.replace(tzinfo=default_tzinfo)
    # seconds from epoch (01-Jan-1970 00:00:00 in the dt's timezone)
    epoch = datetime(1970, 1, 1, tzinfo=dt.tzinfo)
    ts = int((dt.astimezone(dt.tzinfo) - epoch).total_seconds())
    # seconds to milliseconds
    return int(1000*ts + dt.microsecond/1000)

def iso8601_to_fixed_ts(ts, tz="GMT"):
    """
    The format of datetime string in Timestamp(ISO) of export.csv that
    the TP wireless logger generates is like below:
        "2018-07-10T07:02:53.917Z"
    It needs to convert into a local time
    as it is likely a JSON-like object sent by TP.
        "2018-07-10T16:02:53.917+09:00"
    The superset recoginizes below format:
        "2018-07-10 16:02:53.917+09:00"
    """
    dt = dateutil.parser.parse(ts)
    dt = dt.astimezone(dateutil.tz.gettz(tz))
    # for python 3.5
    #return dt.isoformat(sep=" ", timespec="milliseconds")
    return dt.isoformat()

