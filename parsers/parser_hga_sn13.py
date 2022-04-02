from parser_template import parser_template
from struct import unpack
from time import strftime, gmtime

class parser(parser_template):
    """
    The payload parser for Highgain HG-OK-IOT-SN13
    message format:
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
    """
    def parse_unixtime(self, data):
        """
        unixtime, little endien.
        convert unixtime into ISO8601 naive.
        e.g. 0x58d4b41b -> 2017-03-24T05:52:27
        """
        return strftime("%Y-%m-%dT%H:%M:%S", gmtime(self.parse_number(data)))

    def parse_gis(self, data):
        """
        IEEE 754 into GIS
        e.g. 0x420ea943 -> 35.665295
        """
        return round(unpack(">f", data)[0],5)

    def parse_altitude(self, data):
        return self.parse_number(data)/10

    def parse_speed(self, data):
        return self.parse_number(data)/10

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) != 24:
            return False
        #
        return self.parse_by_format(byte_data, [
            ( "batt", self.parse_number, 0, 2 ),
            ( "temp", self.parse_number, 2, 4 ),
            ( "iso8601", self.parse_unixtime, 4, 8 ),
            ( "lat", self.parse_gis, 8, 12 ),
            ( "lon", self.parse_gis, 12, 16 ),
            ( "altitude", self.parse_altitude, 16, 18 ),
            ( "speed", self.parse_speed, 18, 20 ),
            ( "gyro_x", self.parse_signed_number, 20, 21 ),
            ( "gyro_y", self.parse_signed_number, 21, 22 ),
            ( "gyro_z", self.parse_signed_number, 22, 23 ),
            ])

"""
test code
"""
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 1:
        test_data = [sys.argv[1]]
    else:
        test_data = [
            "0000000058d4b41b420ea943430bbb24021d000000000000",
            "000000005F900CCE420EDE6E430B57B10438000000000000",
            ]
    p = parser()
    p.test(test_data)
