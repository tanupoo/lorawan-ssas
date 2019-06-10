from parser_template import parser_template

class parser(parser_template):
    """
    The payload parser for Globalsat TL-100.
    message format is:
        byte: description
        1: device_type
        1: (7-6) GPS Fix Status (5-0) Report Type
        1: Battery Capacity
        4: latitude (IEEE 754)
        4: longitude (IEEE 754)
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
        e.g. 0x82 -> 0x82 / 64 -> 2
        """
        return self.parse_number(data)//64

    def parse_report_type(self, data):
        """
        e.g. 0x82 -> 0x82 % 64 -> 2
        """
        return self.parse_number(data)%64

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) != 11:
            return False
        #
        return self.parse_by_format(byte_data, [
            ( "device_type", self.parse_nothing, 0, 1 ),
            ( "gps_fix", self.parse_gps_fix, 1, 2 ),
            ( "report_type", self.parse_report_type, 1, 2 ),
            ( "batt", self.parse_number, 2, 3 ),
            ( "lat", self.parse_gis, 3, 7 ),
            ( "lon", self.parse_gis, 7, 11 ),
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
                "008263022034b60854231c",
                "000261022039c508541e9b",
            ]
    #
    p = parser()
    p.test(test_data)
