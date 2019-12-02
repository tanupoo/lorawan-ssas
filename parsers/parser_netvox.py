from struct import unpack
from parser_template import parser_template

class parser(parser_template):
    """
    The payload parser for the device of netvox.
    the specification are in the following document.
    """
    def parse_batt(self, data):
        """
        Battery, 0.1 V, unsigned.
        Battery (1Byte, unit:0.1V):
            Bit7 represent lowbattery
            Bit6-0 represent batteryvoltage
            When Battery is 0x00,it represet is powered by DC/AC powersource
        """
        v = self.parse_number(data)
        lowbattery = v & 0x80
        return round((v&0x7f)/10,1)

    def parse_R711(self, data):
        """
        Device: R711, R712, R718A, R718AB, R710A
        nb_bytes Field
           1     DeviceType: 0x01, 0x0B, 0x13, 0x6E
           1     ReportType: 0x01
           1     Battery, 0.1V
           2     Temperature, Signed, 0.01 C
           2     Humidity, 0.01 %
           3     Reserved
        """
        return self.parse_by_format(data, [
                # function, start byte, end byte
                ( "batt", self.parse_batt, 3, 4 ),
                ( "temp", self.parse_signed_number_d2, 4, 6 ),
                ( "humid", self.parse_number_d2, 6, 8 ),
                ])

    def parse_R726(self, data):
        """
        Device: RA07Series, R726Series, R727Series, RA07ASeries, R726ASeries,
                R727ASeries, R718PASeries, R718PBSeries, R718R, R718U,
                R718SSeries, R728R, R728U, R728S, R729R, R729U, R729S
        nb_bytes Field
           1     DeviceType: 0x05, 0x09, 0x0D, 0x52, 0x53, 0x54, 0x57, 0x58,
                             0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67,
                             0x68
           1     ReportType: 0x01 - 0x09
                 ---- 0x01 ----
           1     Battery 0.1V
           2     PM1.0 1ug/m3
           2     PM2.5 1ug/m3
           2     PM10  1ug/m3
           1     Reserved
                 ---- 0x08 ----
           1     Battery 0.1V
           2     PH 1mV, 0.01pH
           2     TemperaturewithPH, Signed, 0.01
           3     Reserved
            0x08: batt ph  temp orp reserved
                   1    2   2    2      1
        """
        if data[2] == 0x01:
            return self.parse_by_format(data, [
                    # function, start byte, end byte
                    ( "batt", self.parse_batt, 3, 4 ),
                    ( "pm_1_0", self.parse_number, 4, 6 ),
                    ( "pm_2_5", self.parse_number, 6, 8 ),
                    ( "pm_10", self.parse_number, 8, 10 ),
                    ])
        elif data[2] == 0x02:
            return self.parse_by_format(data, [
                    # function, start byte, end byte
                    ( "batt", self.parse_batt, 3, 4 ),
                    ( "pm_1_0", self.parse_number, 4, 6 ),
                    ( "pm_2_5", self.parse_number, 6, 8 ),
                    ( "pm_10", self.parse_number, 8, 10 ),
                    ])
        elif data[2] == 0x08:
            return self.parse_by_format(data, [
                    # function, start byte, end byte
                    ( "batt", self.parse_batt, 3, 4 ),
                    ( "ph", self.parse_number_d2, 4, 6 ),
                    ( "temp_with_ph", self.parse_signed_number_d2, 6, 8 ),
                    ])
        else:
            print("ERROR: unsupported DataType {} for DeviceType {} of netvox"
                  .format(data[2],data[1]))
            return False

    def parse_R718IA2(self, data):
        """
        Device: R718IA2, R718IB2, R730IA2, R730IB2
        nb_bytes Field
           1     DeviceType: 0x41, 0x42, 0x76, 0x77
           1     ReportType: 0x01
           1     Battery, 0.1V
           2     ADCRawValue1, 1mV
           2     ADCRawValue2, 1mV
           3     Reserved
        """
        if data[2] == 0x01:
            return self.parse_by_format(data, [
                    # function, start byte, end byte
                    ( "batt", self.parse_batt, 3, 4 ),
                    ( "adc_raw_value_1", self.parse_number, 4, 6 ),
                    ( "adc_raw_value_2", self.parse_number, 6, 8 ),
                    ])
        else:
            print("ERROR: unsupported DataType {} for DeviceType {} of netvox"
                  .format(data[2],data[1]))
            return False

    def parse_xgen(self, data):
        """
        For general purpose.
        nb_bytes Field
           1     Version
           1     DeviceType
           1     ReportType
           8     NetvoxPayLoadData
        """
        return self.parse_by_format(data, [
                ( "Version", self.parse_number, 0, 1 ),
                ( "DeviceType", self.parse_number, 1, 2 ),
                ( "ReportType", self.parse_number, 2, 3 ),
                ( "Payload", self.parse_hex, 3, 11 ),
                ])

    def parse_bytes(self, byte_data):
        """
        byte_data: payload in bytes.
        return a dict object.
        """
        format_tab = [
                { "type": 0x01, "parser": self.parse_R711 }, # R711, R712
                { "type": 0x02, "parser": self.parse_xgen }, # R311A
                { "type": 0x03, "parser": self.parse_xgen }, # RB11E
                { "type": 0x04, "parser": self.parse_xgen }, # R311G
                { "type": 0x05, "parser": self.parse_R726 }, # RA07Series
                { "type": 0x06, "parser": self.parse_xgen }, # R311W
                { "type": 0x07, "parser": self.parse_xgen }, # RB11E1
                { "type": 0x08, "parser": self.parse_xgen }, # R801A
                { "type": 0x09, "parser": self.parse_R726 }, # R726Series
                { "type": 0x0A, "parser": self.parse_xgen }, # RA02A
                { "type": 0x0B, "parser": self.parse_R711 }, # R718A
                { "type": 0x0C, "parser": self.parse_xgen }, # RA07W
                { "type": 0x0D, "parser": self.parse_R726 }, # R727Series
                { "type": 0x0E, "parser": self.parse_xgen }, # R809A
                { "type": 0x0F, "parser": self.parse_xgen }, # R211
                { "type": 0x10, "parser": self.parse_xgen }, # RB02I
                { "type": 0x11, "parser": self.parse_xgen }, # RA02C
                { "type": 0x12, "parser": self.parse_xgen }, # R718WB
                { "type": 0x13, "parser": self.parse_R711 }, # R718AB
                { "type": 0x14, "parser": self.parse_xgen }, # R718B2
                { "type": 0x15, "parser": self.parse_xgen }, # R718CJ2
                { "type": 0x16, "parser": self.parse_xgen }, # R718CK2
                { "type": 0x17, "parser": self.parse_xgen }, # R718CT2
                { "type": 0x18, "parser": self.parse_xgen }, # R718CR2
                { "type": 0x19, "parser": self.parse_xgen }, # R718CE2
                { "type": 0x1A, "parser": self.parse_xgen }, # R718DA
                { "type": 0x1B, "parser": self.parse_xgen }, # R718DB
                { "type": 0x1C, "parser": self.parse_xgen }, # R718E
                { "type": 0x1D, "parser": self.parse_xgen }, # R718F
                { "type": 0x1E, "parser": self.parse_xgen }, # R718G
                { "type": 0x1F, "parser": self.parse_xgen }, # R718H
                { "type": 0x20, "parser": self.parse_xgen }, # R718IA
                { "type": 0x21, "parser": self.parse_xgen }, # R718J
                { "type": 0x22, "parser": self.parse_xgen }, # R718KA
                { "type": 0x23, "parser": self.parse_xgen }, # R718KB
                { "type": 0x24, "parser": self.parse_xgen }, # R718LA
                { "type": 0x25, "parser": self.parse_xgen }, # R718LB
                { "type": 0x26, "parser": self.parse_xgen }, # R718MA
                { "type": 0x27, "parser": self.parse_xgen }, # R718MBA
                { "type": 0x28, "parser": self.parse_xgen }, # R718MC
                { "type": 0x29, "parser": self.parse_xgen }, # R718N
                { "type": 0x2A, "parser": self.parse_xgen }, # R718IB
                { "type": 0x2B, "parser": self.parse_xgen }, # R718MBB
                { "type": 0x2C, "parser": self.parse_xgen }, # R718MBC
                { "type": 0x2D, "parser": self.parse_xgen }, # R7185N
                { "type": 0x2E, "parser": self.parse_xgen }, # R718B4
                { "type": 0x2F, "parser": self.parse_xgen }, # R718DA2
                { "type": 0x30, "parser": self.parse_xgen }, # R718S
                { "type": 0x31, "parser": self.parse_xgen }, # R718T
                { "type": 0x32, "parser": self.parse_xgen }, # R718WA
                { "type": 0x33, "parser": self.parse_xgen }, # R718WD
                { "type": 0x34, "parser": self.parse_xgen }, # R718X
                { "type": 0x35, "parser": self.parse_xgen }, # RA0716
                { "type": 0x36, "parser": self.parse_xgen }, # R72616
                { "type": 0x37, "parser": self.parse_xgen }, # R72716alias
                { "type": 0x38, "parser": self.parse_xgen }, # R718CJ4
                { "type": 0x39, "parser": self.parse_xgen }, # R718CK4
                { "type": 0x3A, "parser": self.parse_xgen }, # R718CT4
                { "type": 0x3B, "parser": self.parse_xgen }, # R718CR4
                { "type": 0x3C, "parser": self.parse_xgen }, # R718CE4
                { "type": 0x3D, "parser": self.parse_xgen }, # R718DB2
                { "type": 0x3E, "parser": self.parse_xgen }, # R718F2
                { "type": 0x3F, "parser": self.parse_xgen }, # R718H2
                { "type": 0x40, "parser": self.parse_xgen }, # R718H4
                { "type": 0x41, "parser": self.parse_R718IA2 }, # R718IA2
                { "type": 0x42, "parser": self.parse_R718IA2 }, # R718IB2
                { "type": 0x43, "parser": self.parse_xgen }, # R718J2
                { "type": 0x44, "parser": self.parse_xgen }, # R718KA2
                { "type": 0x45, "parser": self.parse_xgen }, # R718LB2
                { "type": 0x46, "parser": self.parse_xgen }, # R718WA2
                { "type": 0x47, "parser": self.parse_xgen }, # R718WB2
                { "type": 0x48, "parser": self.parse_xgen }, # R718T2
                { "type": 0x49, "parser": self.parse_xgen }, # R718N1
                { "type": 0x4A, "parser": self.parse_xgen }, # R718N3
                { "type": 0x4B, "parser": self.parse_xgen }, # R311B
                { "type": 0x4C, "parser": self.parse_xgen }, # R311CA
                { "type": 0x4D, "parser": self.parse_xgen }, # R312A
                { "type": 0x4E, "parser": self.parse_xgen }, # R311D
                { "type": 0x4F, "parser": self.parse_xgen }, # R311FA
                { "type": 0x50, "parser": self.parse_xgen }, # R311FB
                { "type": 0x51, "parser": self.parse_xgen }, # R311FC
                { "type": 0x52, "parser": self.parse_R726 }, # RA07ASeries
                { "type": 0x53, "parser": self.parse_R726 }, # R726ASeries
                { "type": 0x54, "parser": self.parse_R726 }, # R727ASeries
                { "type": 0x55, "parser": self.parse_xgen }, # R312
                { "type": 0x56, "parser": self.parse_xgen }, # R311CB
                { "type": 0x57, "parser": self.parse_R726 }, # R718PASeries
                { "type": 0x58, "parser": self.parse_R726 }, # R718PBSeries
                { "type": 0x59, "parser": self.parse_xgen }, # R719
                { "type": 0x5A, "parser": self.parse_xgen }, # R311WA
                { "type": 0x5B, "parser": self.parse_xgen }, # R718Q
                { "type": 0x5C, "parser": self.parse_xgen }, # R718IJK
                { "type": 0x5D, "parser": self.parse_xgen }, # R718SA
                { "type": 0x5E, "parser": self.parse_xgen }, # R728SA
                { "type": 0x5F, "parser": self.parse_xgen }, # R729SA
                { "type": 0x60, "parser": self.parse_R726 }, # R718R
                { "type": 0x61, "parser": self.parse_R726 }, # R718U
                { "type": 0x62, "parser": self.parse_R726 }, # R718SSeries
                { "type": 0x63, "parser": self.parse_R726 }, # R728R
                { "type": 0x64, "parser": self.parse_R726 }, # R728U
                { "type": 0x65, "parser": self.parse_R726 }, # R728S
                { "type": 0x66, "parser": self.parse_R726 }, # R729R
                { "type": 0x67, "parser": self.parse_R726 }, # R729U
                { "type": 0x68, "parser": self.parse_R726 }, # R729S
                { "type": 0x69, "parser": self.parse_xgen }, # R602A
                { "type": 0x6A, "parser": self.parse_xgen }, # RA0716A
                { "type": 0x6B, "parser": self.parse_xgen }, # R718WBA
                { "type": 0x6C, "parser": self.parse_xgen }, # R311CC
                { "type": 0x6D, "parser": self.parse_xgen }, # R306
                { "type": 0x6E, "parser": self.parse_R711 }, # R720A
                { "type": 0x6F, "parser": self.parse_xgen }, # R720B
                { "type": 0x70, "parser": self.parse_xgen }, # R720C
                { "type": 0x71, "parser": self.parse_xgen }, # RA10
                { "type": 0x72, "parser": self.parse_xgen }, # R718PC
                { "type": 0x73, "parser": self.parse_xgen }, # R816
                { "type": 0x74, "parser": self.parse_xgen }, # R730IA
                { "type": 0x75, "parser": self.parse_xgen }, # R730IB
                { "type": 0x76, "parser": self.parse_R718IA2 }, # R730IA2
                { "type": 0x77, "parser": self.parse_R718IA2 }, # R730IB2
                { "type": 0x78, "parser": self.parse_xgen }, # R730CJ2
                { "type": 0x79, "parser": self.parse_xgen }, # R730CK2
                { "type": 0x7A, "parser": self.parse_xgen }, # R730CT2
                { "type": 0x7B, "parser": self.parse_xgen }, # R730CR2
                { "type": 0x7C, "parser": self.parse_xgen }, # R730CE2
                { "type": 0x7D, "parser": self.parse_xgen }, # R730F
                { "type": 0x7E, "parser": self.parse_xgen }, # R730F2
                { "type": 0x7F, "parser": self.parse_xgen }, # R730H
                { "type": 0x80, "parser": self.parse_xgen }, # R730H2
                { "type": 0x81, "parser": self.parse_xgen }, # R730MA
                { "type": 0x82, "parser": self.parse_xgen }, # R730MBA
                { "type": 0x83, "parser": self.parse_xgen }, # R730MBB
                { "type": 0x84, "parser": self.parse_xgen }, # R730MBC
                { "type": 0x85, "parser": self.parse_xgen }, # R730WA
                { "type": 0x86, "parser": self.parse_xgen }, # R730WA2
                { "type": 0x87, "parser": self.parse_xgen }, # R730WB
                { "type": 0x88, "parser": self.parse_xgen }, # R730WB2
                { "type": 0x89, "parser": self.parse_xgen }, # R730DA
                { "type": 0x8A, "parser": self.parse_xgen }, # R730DA2
                { "type": 0x8B, "parser": self.parse_xgen }, # R730DB
                { "type": 0x8C, "parser": self.parse_xgen }, # R730DB2
                { "type": 0x8D, "parser": self.parse_xgen }, # R730LB
                { "type": 0x8E, "parser": self.parse_xgen }, # R730LB2
                { "type": 0x8F, "parser": self.parse_xgen }, # R718WE
                { "type": 0x90, "parser": self.parse_xgen }, # R718CJ
                { "type": 0x91, "parser": self.parse_xgen }, # R718CK
                { "type": 0x92, "parser": self.parse_xgen }, # R718CT
                { "type": 0x93, "parser": self.parse_xgen }, # R718CR
                { "type": 0x94, "parser": self.parse_xgen }, # R718CE
                { "type": 0x95, "parser": self.parse_xgen }, # R718B
                { "type": 0x96, "parser": self.parse_xgen }, # R718PD
                { "type": 0xFF, "parser": self.parse_xgen }, # ALL
                ]
        if len(byte_data) != 11:
            print("ERROR: invalid data length for netvox, expected 8 but {}"
                  .format(len(byte_data)))
            return False
        if byte_data[0] != 0x01:
            print("ERROR: unsupported version for netvox, expected 1 but {}"
                  .format(byte_data[0]))
            return False
        for t in format_tab:
            if byte_data[1] == t["type"]:
                d = t["parser"](byte_data)
                if d is False:
                    return False
                else:
                    d["data_type"] = t["type"]
                    return d
        print("ERROR: unknown data type {:02x}".format(byte_data[1]))
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
                { "data": "01 0B 01 24 09EA 1A90 000000",
                 "result": { "batt": 3.6, "temp": 25.38, "humid": 68.0,
                            "data_type": 11 } },
                { "data": "01 0B 01 24 FC18 1A90 000000",
                 "result": { "batt": 3.6, "temp": -10.0, "humid": 68.0,
                            "data_type": 11 } },
                { "data": "01 0B 01 9F 09EA 1A90 000000",
                 "result": { "batt": 3.1, "temp": 25.38, "humid": 68.0,
                            "data_type": 11 } },
                { "data": "01 66 08 9F 09EA 1A9a 000000",
                 "result": { "batt": 3.1, "ph": 25.38,
                            "temp_with_ph": 68.1 } },
                { "data": "01 41 01 9F 09EA 1A9a 000000",
                 "result": { "batt": 3.1, "adc_raw_value_1": 2538,
                            "adc_raw_value_2": 6810 } },
            ]
    #
    p = parser()
    p.test_eval(test_data)
