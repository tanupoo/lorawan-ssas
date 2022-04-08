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
    def parse_gcv(self, data):
        """
        Geographic Coordinate Value
        latitude, longitude, little endien.
        e.g. 0x073dc4db -> 121488603 / 1000000 -> 121.488603
        e.g. 0x63737d01 ->  24996633 / 1000000 ->  24.996633
        """
        return self.parse_number_le(data)/1000000

    def parse_b5to7(self, data):
        """
        Bit5 to Bit7
            - GPS Fix
            - Beacon Type
        e.g. 0x82 -> 0x82 / 32 -> 2
        """
        return self.parse_number(data)//32

    def parse_b0to4(self, data):
        """
        Bit0 to Bit4
            - Report Type
            - Alarm Type
        e.g. 0x82 -> 0x82 % 32 -> 2
        """
        return self.parse_number(data)%32

    #
    # parsers of each protocol
    #
    def parse_track_rep(self, byte_data):
        """
        Tracking Report
        Protocol Version: 0x0C
        Command ID: 0x1002
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) == 17:
            return self.parse_by_format(byte_data, [
                ( "version", self.parse_number, 0, 1 ),
                ( "command_id", self.parse_number, 1, 3 ),
                ( "lat", self.parse_gcv, 3, 7 ),
                ( "lon", self.parse_gcv, 7, 11 ),
                ( "gps_fix", self.parse_b5to7, 11, 12 ),
                ( "report_type", self.parse_b0to4, 11, 12 ),
                ( "batt", self.parse_number, 12, 13 ),
                ( "timestamp", self.parse_number_le, 13, 17 ),
                ])
        else:
            return False

    def parse_track_rep_short(self, byte_data):
        """
        Tracking Report Short
        Protocol Version: 0x80
        Command ID: 0x83
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) == 11:
            return self.parse_by_format(byte_data, [
                ( "version", self.parse_number, 0, 1 ),
                ( "command_id", self.parse_number, 1, 2 ),
                ( "lat", self.parse_gcv, 2, 6 ),
                ( "lon", self.parse_gcv, 6, 10 ),
                ( "gps_fix", self.parse_b5to7, 10, 11 ),
                ( "report_type", self.parse_b0to4, 10, 11 ),
                ])
        else:
            return False

    def parse_help_rep(self, byte_data):
        """
        Help Report
        Protocol Version: 0x0C
        Command ID: 0x0B00
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) == 17:
            return self.parse_by_format(byte_data, [
                ( "version", self.parse_number, 0, 1 ),
                ( "command_id", self.parse_number, 1, 3 ),
                ( "lat", self.parse_gcv, 3, 7 ),
                ( "lon", self.parse_gcv, 7, 11 ),
                ( "gps_fix", self.parse_b5to7, 11, 12 ),
                ( "alarm_type", self.parse_b0to4, 11, 12 ),
                ( "batt", self.parse_number, 12, 13 ),
                ( "timestamp", self.parse_number_le, 13, 17 ),
                ])
        else:
            return False

    def parse_help_rep_short(self, byte_data):
        """
        Help Report Short
        Protocol Version: 0x80
        Command ID: 0x01
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) == 11:
            return self.parse_by_format(byte_data, [
                ( "version", self.parse_number, 0, 1 ),
                ( "command_id", self.parse_number, 1, 2 ),
                ( "lat", self.parse_gcv, 2, 6 ),
                ( "lon", self.parse_gcv, 6, 10 ),
                ( "gps_fix", self.parse_b5to7, 10, 11 ),
                ( "alarm_type", self.parse_b0to4, 10, 11 ),
                ])
        else:
            return False

    def parse_beacon_track_rep(self, byte_data):
        """
        Beacon Tracking Report
        Protocol Version: 0x0C
        Command ID: 0x1302
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) == 27:
            return self.parse_by_format(byte_data, [
                ( "version", self.parse_number, 0, 1 ),
                ( "command_id", self.parse_number, 1, 3 ),
                ( "beacon_id", self.parse_hex, 3, 23 ),
                ( "beacon_type", self.parse_b5to7, 23, 24 ),
                ( "report_type", self.parse_b0to4, 23, 24 ),
                ( "rssi", self.parse_number, 24, 25 ),
                ( "tx_power", self.parse_number, 25, 26 ),
                ( "batt", self.parse_number, 26, 27 ),
                ])
        else:
            return False

    def parse_beacon_help_rep(self, byte_data):
        """
        Beacon Help Report
        Protocol Version: 0x0C
        Command ID: 0x0700
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) == 27:
            return self.parse_by_format(byte_data, [
                ( "version", self.parse_number, 0, 1 ),
                ( "command_id", self.parse_number, 1, 3 ),
                ( "beacon_id", self.parse_hex, 3, 23 ),
                ( "beacon_type", self.parse_b5to7, 23, 24 ),
                ( "alarm_type", self.parse_b0to4, 23, 24 ),
                ( "rssi", self.parse_number, 24, 25 ),
                ( "tx_power", self.parse_number, 25, 26 ),
                ( "batt", self.parse_number, 26, 27 ),
                ])
        else:
            return False

    def parse_command(self, byte_data):
        """
        Command
        Protocol Version: 0x0C
        Command ID: 0x0600
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) == 9:
            if byte_data[3] & 0x01:
                # Ping
                return self.parse_by_format(byte_data, [
                    ( "version", self.parse_number, 0, 1 ),
                    ( "command_id", self.parse_number, 1, 3 ),
                    ( "command_type", self.parse_hex, 3, 4),
                    ( "gps_interval", self.parse_number, 7, 9 ),
                    ])
            elif byte_data[3] & 0x02:
                # Period Mode
                return self.parse_by_format(byte_data, [
                    ( "version", self.parse_number, 0, 1 ),
                    ( "command_id", self.parse_number, 1, 3 ),
                    ( "command_type", self.parse_hex, 3, 4),
                    ( "report_interval", self.parse_number, 5, 7 ),
                    ])
            elif byte_data[3] & 0x04:
                # Motion Mode
                return self.parse_by_format(byte_data, [
                    ( "version", self.parse_number, 0, 1 ),
                    ( "command_id", self.parse_number, 1, 3 ),
                    ( "command_type", self.parse_hex, 3, 4),
                    ( "moving_interval", self.parse_number, 5, 7 ),
                    ( "static_interval", self.parse_number, 7, 9 ),
                    ])
            else:
                self.logger.error("unknown command type {:02x}".format(byte_data[3]))
                return False
        else:
            return False

    def parse_dismiss_help_rep(self, byte_data):
        """
        Dismiss Help Report
        Protocol Version: 0x0C
        Command ID: 0x1102
        byte_data: payload in bytes.
        return a dict object.
        """
        if len(byte_data) == 12:
            return self.parse_by_format(byte_data, [
                ( "version", self.parse_number, 0, 1 ),
                ( "command_id", self.parse_number, 1, 3 ),
                ( "stop_help_rep", self.parse_number, 11, 12 ),
                ])
        else:
            return False

    def parse_set_device(self, byte_data):
        """
        Set Device
        Protocol Version: 0x0C
        Command ID: 0x0800
        byte_data: payload in bytes.
        return a dict object.
        """
        if byte_data[-2:].hex() == "0d0a":
            # the length of this command is not fixed.
            com_len = byte_data[3]
            return self.parse_by_format(byte_data, [
                ( "version", self.parse_number, 0, 1 ),
                ( "command_id", self.parse_number, 1, 3 ),
                ( "length", self.parse_number, 3, 4 ),
                ( "command", self.parse_hex, 4, 4 + com_len),
                ])

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes.
        return a dict object.
        """
        if byte_data[0] == 0x0c:
            format_tab = [
                    { "cmd": "1002", "parser": self.parse_track_rep },
                    { "cmd": "0b00", "parser": self.parse_help_rep},
                    { "cmd": "1302", "parser": self.parse_beacon_track_rep },
                    { "cmd": "0700", "parser": self.parse_beacon_help_rep },
                    { "cmd": "0600", "parser": self.parse_command },
                    { "cmd": "1102", "parser": self.parse_dismiss_help_rep },
                    { "cmd": "0800", "parser": self.parse_set_device },
                    ]
            for t in format_tab:
                if byte_data[1:3].hex() == t["cmd"]:
                    return t["parser"](byte_data)
            else:
                self.logger.error("unknown command id {}".format(byte_data[1:3].hex()))
                return False
        elif byte_data[0] == 0x80:
            if byte_data[1] == 0x83:
                # tracking report, short
                return self.parse_track_rep_short(byte_data)
            elif byte_data[1] == 0x01:
                # help report, short
                return self.parse_help_rep_short(byte_data)
            else:
                self.logger.error("unknown short command type {:02x}".
                      format(byte_data[1]))
                return False
        else:
            self.logger.error("unknown protocol version {:02x}".format(byte_data[0]))
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
                # Tracking Report
                "0c 1002 dbc43d07 63737d01 22 64 A4989659",
                # Tracking Report, Short
                "80 83 8dc13d07 016a7d01 44",
                # Help Report
                "0C 0B00 58C23D07 A56A7D01 01 64 649A9659",
                # Help Report, Short
                "80 01 85C03D07 8D6A7D01 01",
                # Beacon Report
                "0C 1302 74278BDAB64445208F0C720EAF05993500000000 22 00 C5 64",
                # Beacon Help Report
                "0C 0700 74278BDAB64445208F0C720EAF05993500000000 21 BC C5 64",
                # Ping
                "0C 0600 21 00 0000 0A00",
                # Period Mode
                "0C 0600 02 00 1E00 0000",
                # Motion Mode
                "0C 0600 13 00 1E00 100E",
                # Dismiss Help Report
                "0C 1102 0000000000000000 01",
                # Set Device
                "0C 0800 0A 4c322843443d3129 0D0A",
            ]
    #
    p = parser(debug_level=99)
    p.test(test_data)
