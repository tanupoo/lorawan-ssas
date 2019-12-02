from parser_template import parser_template
from struct import unpack

class parser(parser_template):
    """
    The payload parser for the device of NALTEC.

    payload must be started by Hdr (i.e. data type).
    """

    def parse_vit(self, data):
        """
        Vit, mV * 25 -> 0x00 - 0xff
        e.g. data = 0xff -> 10.2 mV
             data = 0x01 -> 0.04 mV
        """
        return round(self.parse_number(data)/25,2)

    def parse_temp(self, data):
        """
        Temp, -40 to -1 -> 0xd8 - 0xff, 0 to 125 -> 0x00 - 0x7d
        """
        return self.parse_signed_number(data)

    def parse_current_20mA(self, data):
        """
        0x0000 - 0xffff -> 0mA - 20mA
        """
        return int(self.parse_number_le(data) / 0xffff * 20)

    def parse_voltage_10V(self, data):
        """
        0x0000 - 0xffff -> 0V - 10V
        """
        return int(self.parse_number_le(data) / 0xffff * 10)

    def parse_thermocouple(self, data):
        """
        -200 - 1820 C -> 0.0625
        """
        return round(float(self.parse_signed_number_le(data)*0.0625),4)

    def parse_payload_7f(self, byte_data):
        """
        Hdr, Vit, Temp
        """
        if len(byte_data) != 3:
            return False
        return self.parse_by_format(byte_data, [
                # function, start byte, end byte
                ( "hdr", self.parse_number, 0, 1 ),
                ( "vit", self.parse_vit, 1, 2 ),
                ( "temp", self.parse_temp, 2, 3 ),
                ])

    def parse_payload_23(self, byte_data):
        """
        Hdr, Vit, Temp, C-IN1, C-IN2, Vo-IN1, Vo-IN2
        """
        if len(byte_data) != 11:
            return False
        return self.parse_by_format(byte_data, [
                # function, start byte, end byte
                ( "hdr", self.parse_number, 0, 1 ),
                ( "vit", self.parse_vit, 1, 2 ),
                ( "temp", self.parse_temp, 2, 3 ),
                ( "current_input_1", self.parse_current_20mA, 3, 5 ),
                ( "current_input_2", self.parse_current_20mA, 5, 7 ),
                ( "voltage_input_1", self.parse_voltage_10V, 7, 9 ),
                ( "voltage_input_2", self.parse_voltage_10V, 9, 11 ),
                ])

    def parse_payload_24(self, byte_data):
        """
        Hdr, Vit, Temp, TC1, TC2, TC3, TC4
        """
        if len(byte_data) != 11:
            return False
        return self.parse_by_format(byte_data, [
                # function, start byte, end byte
                ( "hdr", self.parse_number, 0, 1 ),
                ( "vit", self.parse_vit, 1, 2 ),
                ( "temp", self.parse_temp, 2, 3 ),
                ( "thermocouple_1", self.parse_thermocouple, 3, 5 ),
                ( "thermocouple_2", self.parse_thermocouple, 5, 7 ),
                ( "thermocouple_3", self.parse_thermocouple, 7, 9 ),
                ( "thermocouple_4", self.parse_thermocouple, 9, 11 ),
                ])

    def parse_payload_00(self, byte_data):
        raise NotImplementedError

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes
        return a dict object.
        """
        format_tab = [
                { "hdr": 0x7f, "parser": self.parse_payload_7f },
                { "hdr": 0x00, "parser": self.parse_payload_00 },
                { "hdr": 0x23, "parser": self.parse_payload_23 },
                { "hdr": 0x24, "parser": self.parse_payload_24 },
                ]
        for t in format_tab:
            if byte_data[0] == t["hdr"]:
                d = t["parser"](byte_data)
                if d is False:
                    return False
                else:
                    d["data_type"] = t["hdr"]
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
                { "data": "7f ff ff",
                 "result": { "hdr": 0x7f, "vit": 10.2, "temp": -1 } },
                { "data": "7f 19 d8",
                 "result": { "hdr": 0x7f, "vit": 1.00, "temp": -40 } },
                { "data": "7f 01 00",
                 "result": { "hdr": 0x7f, "vit": 0.04, "temp": 0 } },
                { "data": "7f 00 7d",
                 "result": { "hdr": 0x7f, "vit": 0.00, "temp": 125 } },
                { "data": "23 7f ff 00 00 ff ff 00 00 ff ff",
                 "result": { "hdr": 0x23, "vit": 5.08, "temp": -1,
                        "current_input_1": 0,
                        "current_input_2": 20,
                        "voltage_input_1": 0,
                        "voltage_input_2": 10, } },
                { "data": "24 00 d8 80 f3 90 fc 90 fc 90 fc",
                 "result": { "hdr": 0x24, "vit": 0.00, "temp": -40,
                        "thermocouple_1": -200.0,
                        "thermocouple_2": -55.0,
                        "thermocouple_3": -55.0,
                        "thermocouple_4": -55.0, } },
                { "data": "24 00 7d ff ff 00 00 c0 71 90 fc",
                 "result": { "hdr": 0x24, "vit": 0.00, "temp": 125,
                        "thermocouple_1": -0.0625,
                        "thermocouple_2": 0.0,
                        "thermocouple_3": 1820.0,
                        "thermocouple_4": -55.0, } },
            ]
    #
    p = parser()
    p.test_eval(test_data)
