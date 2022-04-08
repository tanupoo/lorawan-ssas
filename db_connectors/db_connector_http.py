from db_connector_template import db_connector_template
import requests
import json
from app_util import iso8601_to_ms

class db_connector(db_connector_template):
    """
    this is the database connector for HTTP POST API.

        from db_http import db_connector

        class handler(connector_http):
            pass

        p = handler(logger=self.logger, debug_level=self.debug_level,
                   db_uri="your_rest_api")
        p.submit(kv_data)
    """
    def db_init(self, **kwargs):
        """
        db_uri must be passed.
        """
        self.db_uri = kwargs.get("db_uri")
        if self.db_uri is None:
            raise ValueError("db_uri is required in the handler.")
        return True

    def db_submit(self, kv_data, **kwargs):
        '''
        - submit json data into the MongoDB via REST API.
        - assuming that all keys are exist in the json data.
          because it assumes that proc_tp_uplink() has been called already.
        - assuming that the "ts" key has the ISO8601 string value like below:
            "2017-03-24T06:53:32.502+01:00".
        - if the string looks naive, it will convert into the timezone
          when you specified at calling db_init().
        '''
        kv_data["ts"] = {"$date": iso8601_to_ms(kv_data["ts"])}
        # submit.
        ret = requests.post(self.db_uri, data=json.dumps(kv_data))
        if ret.ok:
            ret_value = ret.json()
            if ret_value["ok"] is True:
                if self.debug_level > 0:
                    self.logger.debug("Succeeded submitting data into MongoDB.")
                    return True
            else:
                self.logger.error("Response from MongoDB: {}".format(ret_value))
                return False
        else:
            self.logger.error("Failed submitting data into MongoDB. {} {} {}"
                .format(ret.status_code, ret.reason, ret.text))
            return False

