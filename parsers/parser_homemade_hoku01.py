from parser_template import parser_template

class parser(parser_template):
    """
    hex_string: application data in hex string.
         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |   H   |                                                       |
        +-+-+-+-+-+-+-+-+-+-+-+-+  Shade or Not  -+-+-+-+-+-+-+-+-+-+-+-+
        |                                                               |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |          Temperature          |           Humidity            |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    
         0                   1           
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |S|   Integer   |    Decimal    |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """
    def parse_h(self, data):
        """
        XXX header ? reserved ?
        """
        return ((self.parse_number(data))>>4)&0x0f

    def parse_shaded(self, data):
        """
        return a sequence of 0 or 1 of 60 as string data like "001001100..."
        1 means shaded.
        XXX the most right bit is newer ?
        """
        # mask the first 4 bits.
        shade_or_not = data
        shade_or_not = shade_or_not[0]&0x0f
        s = []
        for i in range(60):
            s.append("0" if shade_or_not&1 == 0 else "1")
            shade_or_not >>= 1
        return "".join(reversed(s))

    def parse_temp(self, data):
        temp_sign = 1 if data[0]&0x8 == 0 else -1
        temp = (data[0]&0x7f) + data[1]/100
        return temp_sign * temp

    def parse_humid(self, data):
        return data[0] + data[1]/100

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes
        return a dict object.
        """
        raise NotImplementedError("XXX need to be reimplemented.")
        # XXX
        if len(byte_data) != 12:
            print("ERROR: the data length is not 12.")
            return False
        return self.parse_by_format(byte_data, [
                ( "h", self.parse_h, 0, 1 ),
                ( "shaded", self.parse_shaded, 0, 8 ),
                ( "temp", self.parse_temp, 8, 10 ),
                ( "humid", self.parse_humid, 10, 12 )
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
                "0ffffffeffffff3f21002300",
                "0fffffefffffff3fa1002400"
            ]
    #
    p = parser()
    p.test(test_data)
