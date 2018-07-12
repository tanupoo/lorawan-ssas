# -*- coding: utf-8 -*-

from __future__ import print_function

import requests
import json
from app_util import default_logger
from datetime_timestamp import *

db_url = "http://127.0.0.1:28017/lorawan/app/"

class parser():

    @classmethod
    def parse(cls, hex_string):
        return None

    def __init__(self, **kwargs):
        self.logger = kwargs.get("logger", default_logger)
        self.debug_level = kwargs.get("debug_level", 0)

    def submit(self, kv_data, **kwargs):
        '''
        - submit json data into the MongoDB via REST API.
        - assuming that all keys are exist in the json data.
          because it assumes that proc_tp_uplink() has been called already.
        - assuming that the ISO8601 time string is converted into MongoDB
          timestamp.
        '''
        kv_data["DevEUI_uplink"]["Time"] = {"$date":iso8601_to_timestamp_ms(
                                            kv_data["DevEUI_uplink"]["Time"])}
        # submit.
        ret = requests.post(db_url, data=json.dumps(kv_data))
        if ret.ok:
            ret_value = ret.json()
            if ret_value["ok"] is True:
                if self.debug_level > 0:
                    self.logger.debug("Submitting data into MongoDB succeeded.")
                    return True
            else:
                self.logger.error("Response from MongoDB: {}".format(ret_value))
                return False
        else:
            self.logger.error("Submitting data into MongoDB failed. {} {} {}"
                .format(ret.status_code, ret.reason, ret.text))
            return False

