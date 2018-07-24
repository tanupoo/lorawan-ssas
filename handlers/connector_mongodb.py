# -*- coding: utf-8 -*-

import requests
import json
from app_util import iso8601_to_ms
from handler_template import handler_template

class connector_mongodb(handler_template):

    '''
    you can use the following code to submit data into the default
    mongodb.

        from connector_mongodb import connector_mongodb

        class handler(connector_mongodb):
            pass

        p = handler(logger=self.logger, debug_level=self.debug_level,
                   db_uri="your_mongodb_rest_api")
        p.submit(kv_data)

    '''
    def db_init(self, **kwargs):
        '''
        db_uri must be passed.
        '''
        db_uri = kwargs.get("db_uri")
        if db_uri is None:
            raise ValueError("db_uri is required in the handler.")
        self.db_uri = db_uri
        return True

    def db_submit(self, kv_data, **kwargs):
        '''
        - submit json data into the MongoDB via REST API.
        - assuming that all keys are exist in the json data.
          because it assumes that proc_tp_uplink() has been called already.
        - assuming that the "Time" key has the ISO8601 string value like below:
            "2017-03-24T06:53:32.502+01:00".
        - if the string looks naive, it will convert into the timezone
          when you specified at calling db_init().
        '''
        kv_data["Time"] = {"$date": iso8601_to_ms(kv_data["Time"])}
        # submit.
        ret = requests.post(self.db_uri, data=json.dumps(kv_data))
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

