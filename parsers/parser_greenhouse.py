from parser_template import parser_template
from struct import unpack

class parser(parser_template):
    """
    The payload parser for the device of Greenhouse.

    payload types supported.
        1: FMT, SEQ, BAT, PRSW, TIP, KND
        4: FMT, SEQ, BAT, TMP, HUM, LAT, LNG, ACX, ACY, ACZ, PRS
    XXX to be assigned.
       10: FMT, SEQ, BAT, ETMP, RHUM, LAT, LNG, GTMP, WTMP, WBGT, DMY
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

    def parse_prsw(self, data):
        """
        PRS (PRSW), water pressure, float (pressure in water), little endien
        data = b'\x75\xe3\x03\x41'
        >>> round(unpack("<f",data)[0]*1000/9.8,5)
        841.12566 kPa
        """
        return round(unpack("<f",data)[0]*1000/9.8,5)

    def parse_tip(self, data):
        """
        TIP, unsigned, big endien.
        e.g. 0x00000003 -> 3 times.
        """
        return unpack(">I",data)[0]

    def parse_payload_01(self, data):
        """
        01 10 8e 75e30341 00000003 01
        FMT, SEQ, BAT, PRS(PRSW), TIP, KND
        """
        if len(data) != 12:
            return False
        return self.parse_by_format(data, [
                # function, start byte, end byte
                ( "seq", self.parse_number, 1, 2 ),
                ( "batt", self.parse_bat, 2, 3 ),
                ( "w_pressure", self.parse_prsw, 3, 7 ),
                ( "tip", self.parse_tip, 7, 11 ),
                ( "kind", self.parse_number, 11, 12 )
                ])

    def parse_payload_04(self, data):
        """
        for MSNLRA.
        04 0a 8e 0803 0119 32b325 635a08 ffca 0002 002c 2821
        FMT, SEQ, BAT, TMP, HUM, LAT, LNG, ACX, ACY, ACZ, PRS
        """
        if len(data) != 21:
            return False
        return self.parse_by_format(data, [
                # function, start byte, end byte
                ( "seq", self.parse_number, 1, 2 ),
                ( "batt", self.parse_bat, 2, 3 ),
                ( "temp", self.parse_temp, 3, 5 ),
                ( "humid", self.parse_humid, 5, 7 ),
                ( "lat", self.parse_lat, 7, 10 ),
                ( "lon", self.parse_lon, 10, 13 ),
                ( "accel_x", self.parse_ac, 13, 15 ),
                ( "accel_y", self.parse_ac, 15, 17 ),
                ( "accel_y", self.parse_ac, 17, 19 ),
                ( "pressure", self.parse_prs, 19, 21 )
                ])

    def parse_payload_10(self, data):
        """
        for 401D.
        0a 10 00 0803 0119 000000 000000 0805 0806 0807 0000
        FMT, SEQ, BAT, ETMP, RHUM, LAT, LNG, GTMP, WTMP, WBGT, DMY
        """
        if len(data) != 21:
            return False
        return self.parse_by_format(data, [
                # function, start byte, end byte
                ( "seq", self.parse_number, 1, 2 ),
                ( "temp", self.parse_temp, 3, 5 ),
                ( "humid", self.parse_humid, 5, 7 ),
                ( "gtmp", self.parse_temp, 13, 15 ),
                ( "wtmp", self.parse_temp, 15, 17 ),
                ( "wbgt", self.parse_temp, 17, 19 ),
                ])

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes
        return a dict object.
        """
        format_tab = [
                { "type": 0x0a, "parser": self.parse_payload_10 },
                { "type": 0x04, "parser": self.parse_payload_04 },
                { "type": 0x01, "parser": self.parse_payload_01 },
                ]
        for t in format_tab:
            if byte_data[0] == t["type"]:
                d = t["parser"](byte_data)
                if d is False:
                    return False
                else:
                    d["data_type"] = t["type"]
                    return d
        print("ERROR: unknown data type {:02x}".format(byte_data[0]))
        return False

"""
test code
"""
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 1:
        test_data = [sys.argv[1]]
    else:
        test_data = [
            "0a 0b 00 0803 0119 000000 000000 0804 0805 0806 0000",
            "04 0a 8e 0803 0119 32b325 635a08 ffca 0002 002c 2821",
            "01 10 8e 75e30341 00000003 01",
            "01 10 8e 75e30341 00000003", # error
            ]
    #
    p = parser()
    p.test(test_data)
