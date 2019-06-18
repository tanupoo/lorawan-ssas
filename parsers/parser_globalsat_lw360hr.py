from parser_template import parser_template
import time

class parser(parser_template):
    """
    The payload parser for Globalsat LW-360HR.
    return a dict type.
        byte: description
        2: Protocol Version
        2: Command ID (0226:periodical, 0025:alarm)
        4: Longitude (IEEE 754)
        4: Latitude (IEEE 754)
        1: GPS Fix Status
        1: Reserved
        2: Calorie
        1: Battery Capacity
        4: Date & Time ()
        20: Beacon ID
        1: Beacon Type
        1: RSSI
        1: TxPower
        1: Heart Rate
        2: Skin Temperature
        2: Step Count
        2: Distance
    """
    def parse_gis(self, data):
        """
        latitude, longitude, little endien.
        e.g. 0x79967e08 -> 142.513785
        """
        return self.parse_number_le(data)/1000000

    def parse_gps_fix(self, data):
        return self.parse_number(data)//32

    def parse_report_type(self, data):
        return self.parse_number(data)%32

    def parse_beacon_type(self, data):
        return self.parse_number(data)//32

    def parse_rssi(self, data):
        """
        RSSI
        e.g. 0xd1 -> 1101 0001 -> 0010 1110 -> 0010 1111 -> 47 -> -47
        The representation range of RSSI is -256 to -1.
        """
        return -1*(((~self.parse_number(data))&0xff)+1)

    def parse_skin_temp(self, data):
        """
        Skin Temperature
        e.g. 0x2c0b -> 28.6
        """
        return round(self.parse_number_le(data)/100,2)

    def parse_unixtime(self, data):
        """
        unixtime, little endien.
        convert unixtime into ISO8601 naive.
        e.g. 58d4b41b -> 2017-03-24T05:52:27
        """
        return time.strftime("%Y-%m-%dT%H:%M:%S",
            time.gmtime(self.parse_number_le(data)))

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) != 50:
            return False
        #
        return self.parse_by_format(byte_data, [
            ( "ver", self.parse_number, 0, 1 ),
            ( "cmd_id", self.parse_number, 1, 3 ),
            ( "lon", self.parse_gis, 3, 7 ),
            ( "lat", self.parse_gis, 7, 11 ),
            ( "gps_fix", self.parse_gps_fix, 11, 12 ),
            ( "report_type", self.parse_report_type, 11, 12 ),
            ( "reserved", None, 12, 13 ),
            ( "calorie", self.parse_number_le, 13, 15 ),
            ( "batt", self.parse_number, 15, 16 ),
            ( "dev_ts", self.parse_unixtime, 16, 20 ),
            ( "beacon_id", self.parse_nothing, 20, 40 ),
            ( "beacon_type", self.parse_beacon_type, 40, 41 ),
            ( "dev_rssi", self.parse_rssi, 41, 42 ),
            ( "dev_txpw", self.parse_number, 42, 43 ),
            ( "heart_rate", self.parse_number, 43, 44 ),
            ( "skin_temp", self.parse_skin_temp, 44, 46 ),
            ( "step_count", self.parse_number_le, 46, 48 ),
            ( "step_distance", self.parse_number_le, 48, 50 ),
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
                """
                0c 2702 372e4e08 52fe2002 42 2b 5b01 5f 9a11ee5c 0000000000000000000000000000000000000000 00 00 00 4b 620c bf01 6f03
                """,
                """
                0c 2702 ee314e08 de002102 02 00 c301 5a b81dee5c 0000000000000000000000000000000000000000 00 00 00 5b 540b 8708 5108
                """,
            ]
    #
    p = parser()
    p.test(test_data)
