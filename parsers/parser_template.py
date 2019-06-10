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

    def parse_signed_number(self, data):
        """
        convert bytes in big endien into a signed number.
        """
        return int.from_bytes(data,"big",signed=True)

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
