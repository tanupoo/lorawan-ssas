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
            "7f ff ff", #  10.2 mV,  -1 C
            "7f 19 d8", #  1.00 mV, -40 C
            "7f 01 00", #  0.04 mV,   0 C
            "7f 00 7d", #  0.00 mV, 125 C
            ]
    #
    p = parser()
    p.test(test_data)
