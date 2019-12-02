from struct import unpack
from parser_template import parser_template

class parser(parser_template):
    """
    The payload parser for the device of Yokogawa..
    the specification are in the following document.
        https://www.yokogawa.co.jp/solutions/solutions/iiot/maintenance/sushi-sensor-j/#%E3%83%89%E3%82%AD%E3%83%A5%E3%83%A1%E3%83%B3%E3%83%88%EF%BC%86%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89

    """

    def parse_x10(self, data):
        '''
        0x10 Z
        0x11 XYZ
        10 0000 39e1 354a 4f10
        b'\x00\x00',-668.5,12.4140625,0.0005259513854980469
        '''
        return {
            "status": data[1:3],
            "accel": self.parse_binary16_to_float(data[3:5]),
            "velocity": self.parse_binary16_to_float(data[5:7]),
            "temp": self.parse_binary16_to_float(data[7:9]) }

    def parse_x12(self, data):
        '''
        0x12 X
        0x13 Y
        '''
        return {
            "status": data[1:3],
            "accel": self.parse_binary16_to_float(data[3:5]),
            "velocity": self.parse_binary16_to_float(data[5:7]) }

    def parse_x40(self, data):
        return {
            "uptime": unpack(">I",b"\x00"+data[1:4])[0],
            "battery": data[4]/2,
            "rssi": -1*data[5],
            "per": data[6],
            "snr": data[7]/4 }

    def parse_x41(self, data):
        return {
            "status": "".join(["{:02x}".format(i) for i in data[1:5]]),
            "detail": "".join(["{:02x}".format(i) for i in data[5:9]]) }

    def parse_x42(self, data):
        return {
            "tag": data[1:11] }

    def parse_x43(self, data):
        return {
            "lon": unpack(">f",data[1:5])[0],
            "lat": unpack(">f",data[5:9])[0] }

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes.
        return a dict object.
        """
        format_tab = [
                { "type": 0x10, "parser": self.parse_x10 },
                { "type": 0x11, "parser": self.parse_x10 }, # XXX need to check.
                { "type": 0x12, "parser": self.parse_x12 },
                { "type": 0x13, "parser": self.parse_x12 },
                { "type": 0x40, "parser": self.parse_x40 },
                { "type": 0x41, "parser": self.parse_x41 },
                { "type": 0x42, "parser": self.parse_x42 },
                { "type": 0x43, "parser": self.parse_x43 },
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
            "1000003a1134d85028",
            "10000039e1354a4f10",
            ]
    #
    p = parser()
    p.test(test_data)
