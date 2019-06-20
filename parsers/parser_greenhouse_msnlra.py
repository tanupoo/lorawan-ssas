from parser_template import parser_template
from struct import unpack

class parser(parser_template):
    """
    The payload parser for the device of Greenhouse MSNLRA.

    payload types supported.
        SEQ, BAT, TMP, HUM, PRS, LAT, LNG, ACX, ACY, ACZ, ANX, ANY, ANZ
    """

    def parse_bat(self, data):
        """
        BAT, 0% to 100% -> 0xfe to 0x01
        e.g. data = 0x8e -> bat = 56 %
        """
        return round((self.parse_number(data)/254)*100)

    def parse_temp(self, data):
        """
        TMP, unit 0.01 degrees, signed.
        e.g. data = 0x0803 -> 20.51 C
        """
        return round(self.parse_number(data)/100,2)

    def parse_humid(self, data):
        """
        HUM, unit 0.1 %, unsigned.
        e.g. data = 0x0119 -> 28.1 %
        """
        return round(self.parse_number(data)/10,1)

    def parse_lat(self, data):
        return round((self.parse_number(data)/pow(2,23))*90,5)

    def parse_lon(self, data):
        return round((self.parse_number(data)/pow(2,23))*180,5)

    def parse_ac(self, data):
        """
        ACX, ACY, ACZ, unit 10mg, signed.
        e.g. 0xffca -> -540 mg
        """
        return self.parse_signed_number(data)*10

    def parse_prs(self, data):
        """
        PRS, unit 0.1 hPa. unsigned.
        e.g. 0x2821 -> 1027.3 hPa
        """
        return round(self.parse_number(data)/10,1)

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes
        return a dict object.
        """
        if len(byte_data) != 26:
            return False
        return self.parse_by_format(byte_data, [
                # function, start byte, end byte
                ( "seq", self.parse_number, 0, 1 ),
                ( "batt", self.parse_bat, 1, 2 ),
                ( "temp", self.parse_temp, 2, 4 ),
                ( "humid", self.parse_humid, 4, 6 ),
                ( "pressure", self.parse_prs, 6, 8 ),
                ( "lat", self.parse_lat, 8, 11 ),
                ( "lon", self.parse_lon, 11, 14 ),
                ( "accel_x", self.parse_ac, 14, 16 ),
                ( "accel_y", self.parse_ac, 16, 18 ),
                ( "accel_x", self.parse_ac, 18, 20 ),
                ( "angle_x", self.parse_ac, 20, 22 ),
                ( "angle_y", self.parse_ac, 22, 24 ),
                ( "angle_z", self.parse_ac, 24, 26 ),
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
            "00 f3 0b59 01cf 26f1 000000 000000 0007 fffd ff95 0176 ff31 de85",
            "01 f3 0b62 01cf 26f1 000000 000000 0005 fffb ff9e 013d feda de8a",
            "02 f3 0b6b 01cd 26f1 000000 000000 0005 fffb ff9d 0151 feaf deb6",
            "03 f1 0b76 01cb 26f2 000000 000000 0004 fffe ff9f 00fa ff78 ddf6",
            "04 f1 0b7b 01ca 26f1 000000 000000 0008 fff9 ff97 01e5 fe5a df5d",
            ]
    #
    p = parser()
    p.test(test_data)
