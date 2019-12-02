from binascii import a2b_hex
from app_util import default_logger

class parser_template():

    def __init__(self, **kwargs):
        """
        kwargs must contain: logger, debug_level
        """
        self.logger = kwargs.get("logger", default_logger)
        self.debug_level = kwargs.get("debug_level", 0)

    def parse_by_format(self, data, format_tab):
        """
        parse the bytes data according to the format table passed.
        data: byte data.
        format_tab: the structure of the format table is a list like below:
            a dict key, a function, start byte, end byte
            e.g. [ ..., ( "accel_x", self.parse_acx, 13, 15 ), ... ]
        """
        ret = {}
        for f in format_tab:
            if f[1] is not None:
                ret.update({ f[0]: f[1](data[f[2]:f[3]]) })
        return ret

    def parse_number(self, data):
        """
        convert bytes in big endien into a unsigned number.
        """
        return int.from_bytes(data,"big")

    def parse_number_d1(self, data):
        """
        convert bytes in big endien into a unsigned number with unit of 0.1.
        """
        return round(int.from_bytes(data,"big")/10,1)

    def parse_number_d2(self, data):
        """
        convert bytes in big endien into a unsigned number with unit of 0.01.
        """
        return round(int.from_bytes(data,"big")/100,2)

    def parse_signed_number(self, data):
        """
        convert bytes in big endien into a signed number.
        """
        return int.from_bytes(data,"big",signed=True)

    def parse_signed_number_d1(self, data):
        """
        convert bytes in big endien into a signed number with unit of 0.1.
        """
        return round(int.from_bytes(data,"big",signed=True)/10,1)

    def parse_signed_number_d2(self, data):
        """
        convert bytes in big endien into a signed number with unit of 0.01.
        """
        return round(int.from_bytes(data,"big",signed=True)/100,2)

    def parse_number_le(self, data):
        """
        convert bytes in little endien into a unsigned number.
        """
        return int.from_bytes(data,"little")

    def parse_signed_number_le(self, data):
        """
        convert bytes in little endien into a signed number.
        """
        return int.from_bytes(data,"little",signed=True)

    def parse_nothing(self, data):
        """
        return data as it is.
        """
        return data

    def parse_bytes(self, byte_data):
        """
        TEMPLATE should be overwritten.
        parse the payload in bytes and return a Python dict object.
        """
        raise NotImplementedError

    def parse_hex(self, hex_string):
        """
        - parse the payload in hex string and return a Python dict object.
        - the return value:
            + None: ignore parsing.
            + False: something error happened.
            + Others: a Python dict should be put in KEY_APP_DATA.
        """
        # check whether it should be ignored.
        # this is to compare a **string** of "None", not the None object.
        if hex_string == "None":
            return None
        return self.parse_bytes(a2b_hex(hex_string))

    def parse_binary16_to_float(self, data):
        # referred to https://gist.github.com/zed/59a413ae2ed4141d2037
        assert 2 == len(data) and isinstance(data, bytes)
        n = int.from_bytes(data,"big")
        sign = n >> 15
        exp = (n >> 10) & 0b011111
        fraction = n & (2**10 - 1)
        if exp == 0:
            if fraction == 0:
                return -0.0 if sign else 0.0
            else:
                return (-1)**sign * fraction / 2**10 * 2**(-14)  # subnormal
        elif exp == 0b11111:
            if fraction == 0:
                return float('-inf') if sign else float('inf')
            else:
                return float('nan')
        return (-1)**sign * (1 + fraction / 2**10) * 2**(exp - 15)

    def test_eval(self, test_data):
        """
        test_data: a list of test data in hex string.
            e.g. [ { "data":"01020304", "result": { "temp:...} }, ... ]
        """
        for s in test_data:
            if not ("data" in s and "result" in s):
                print("ERROR: invalid data, both data and result must exist.")
            s["data"] = "".join(s["data"].split())
            print("TEST:", s["data"])
            r = self.parse_hex(s["data"]);
            if r is not False:
                for k,v in s["result"].items():
                    if k not in r:
                        print("ERROR: {} must exist in data".format(k))
                        continue
                    print("  {} = {}".format(k,r[k]))
                    if v != r[k]:
                        print("ERROR: invalid value, expected {} but {}"
                              .format(v,r[k]))
                        continue
            else:
                print("  ERROR")

    def test(self, test_data):
        """
        test_data: a list of test data in hex string.
            e.g. [ "01020304", "ffff0000", ... ]
        """
        for s in test_data:
            s = "".join(s.split())
            print("TEST:", s)
            v = self.parse_hex(s);
            if v is not False:
                for k,v in v.items():
                    print("  {} = {}".format(k,v))
            else:
                print("  ERROR")
