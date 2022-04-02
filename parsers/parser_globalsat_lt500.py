from parser_template import parser_template

class parser(parser_template):
    """
    The payload parser for Globalsat LT-500.
    message format is:
        byte: description
        1: Protocol Versioon
        2: Command ID
        4: Longitude (IEEE 754)
        4: Latitude (IEEE 754)
        1: (7-5) GPS Fix Status (4-0) Report Type
        1: Battery Capacity
        4: Date & Time
    """
    def parse_gis(self, data):
        """
        latitude, longitude, big endien.
        e.g. 79 96 7e 08 -> 142.513785
        e.g. 0x017d6b19 -> 24996633 / 1000000 -> 24.996633
        """
        return self.parse_number(data)/1000000

    def parse_gps_fix(self, data):
        """
        e.g. 0x82 -> 0x82 / 32 -> 2
        """
        return self.parse_number(data)//32

    def parse_report_type(self, data):
        """
        e.g. 0x82 -> 0x82 % 32 -> 2
        """
        return self.parse_number(data)%32

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) != 17:
            return False
        #
        return self.parse_by_format(byte_data, [
            ( "version", self.parse_number, 0, 1 ),
            ( "command_id", self.parse_number, 1, 3 ),
            ( "lat", self.parse_gis, 3, 7 ),
            ( "lon", self.parse_gis, 7, 11 ),
            ( "gps_fix", self.parse_gps_fix, 11, 12 ),
            ( "report_type", self.parse_report_type, 11, 12 ),
            ( "batt", self.parse_number, 12, 13 ),
            ( "timestamp", self.parse_number_le, 13, 17 ),
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
                "0c1002dbc43d0763737d012264A4989659",
            ]
    #
    p = parser()
    p.test(test_data)
