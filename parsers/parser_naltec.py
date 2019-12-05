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
        return self.parse_number(data)*25

    def parse_temp(self, data):
        """
        Temp, -40 to -1 -> 0xd8 - 0xff, 0 to 125 -> 0x00 - 0x7d
        """
        return self.parse_signed_number(data)

    def parse_current_20mA(self, data):
        """
        0x0000 - 0xffff -> 0mA - 20mA
        """
        return round(float(self.parse_number_le(data)) / 0xffff * 20, 2)

    def parse_voltage_10V(self, data):
        """
        0x0000 - 0xffff -> 0V - 10V
        """
        return round(float(self.parse_number_le(data)) / 0xffff * 10, 2)

    def parse_thermocouple(self, data):
        """
        from -200 to 1820, unit 0.0625 C
        0xf380 ... 0xfff, 0x000 ... 0x71c0
        i.e.
        int.from_bytes(data, "big", signed=True) * 0.0625
        """
        return self.parse_signed_number(data) * 0.0625

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

    def parse_thermocouple_nope(self, data):
        """
        it means that the terminal is not used.
        """
        return 0x8000

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

    def parse_payload_24x(self, byte_data):
        """
        Hdr, Vit, Temp, TC1, [TC2, [TC3, [TC4]]]
        """
        if len(byte_data) not in [3, 5, 7, 9, 11]:
            return False
        base_format = [
                # function, start byte, end byte
                ( "hdr", self.parse_number, 0, 1 ),
                ( "vit", self.parse_vit, 1, 2 ),
                ( "temp", self.parse_temp, 2, 3 ) ]
        z = len(byte_data)
        for i in range(3, z, 2):
            j = i - 3
            base_format.append(
                    ( "thermocouple_{}".format(j//2+1),
                    self.parse_thermocouple, j+3, j+5))
        for i in range(z, 11, 2):
            j = i - 3
            base_format.append(
                    ( "thermocouple_{}".format(j//2+1),
                    self.parse_thermocouple_nope, 0, 1))
        return self.parse_by_format(byte_data, base_format)

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
                #{ "hdr": 0x24, "parser": self.parse_payload_24 },
                { "hdr": 0x24, "parser": self.parse_payload_24x },
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
                # 0x7f
                { "data": "7f ff ff",
                 "result": { "hdr": 0x7f, "vit": 10.2, "temp": -1 } },
                { "data": "7f 19 d8",
                 "result": { "hdr": 0x7f, "vit": 1.00, "temp": -40 } },
                { "data": "7f 01 00",
                 "result": { "hdr": 0x7f, "vit": 0.04, "temp": 0 } },
                { "data": "7f 00 7d",
                 "result": { "hdr": 0x7f, "vit": 0.00, "temp": 125 } },
            ]
    #
    p = parser()
    p.test_eval(test_data)
    test_data = [
            # 0x23
            "237d120000000090431394",
            "237d12000000007c4fc945",
            "237c0d0000000038940911",
            "237c0c000000009062fc25",
            "237a0b00000000d0283040",
            "23 7a 0a 0000 0000 f578 3b6f",
            ]
    p.test(test_data)
    test_data = [
            # 0x24
            "24760ebf00bf00",
            "24720cbf00c000",
            "24730cc000c300",
            "24730cbb00be00",
            "24730c",
            "24730cbb00",
            "24730cbb00be00",
            "24730c0000bb00be00",
            "24 73 0c f380 ffff 0000 71c0",
            ]
    p.test(test_data)
    """
                # 0x23
                { "data": "237c0c000000009062fc25",
                 "result": { "hdr": 0x23, "vit": 4.96, "temp": 12,
                        "current_input_1": 0,
                        "current_input_2": 0,
                        "voltage_input_1": 3,
                        "voltage_input_2": 1, } },
                { "data": "237a0a00000000f5783b6f",
                 "result": { "hdr": 0x23, "vit": 4.96, "temp": 12,
                        "current_input_1": 0,
                        "current_input_2": 0,
                        "voltage_input_1": 3,
                        "voltage_input_2": 1, } },
                # 0x24
                { "data": "24760ebf00bf00",
                 "result": { "hdr": 0x24, "vit": 4.72, "temp": 14,
                        "thermocouple_1": 11.9375,
                        "thermocouple_2": 11.9375, } },
                { "data": "24 73 0c c000 c300",
                 "result": { "hdr": 0x24, "vit": 4.72, "temp": 14,
                        "thermocouple_1": 11.9375,
                        "thermocouple_2": 11.9375, } },
    """
