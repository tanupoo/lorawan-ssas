from app_util import default_logger
#from app_util import iso8601_to_fixed_ts

class db_connector_template():

    def __init__(self, **kwargs):
        """
        kwargs should contain: logger, debug_level
        """
        self.logger = kwargs.get("logger", default_logger)
        self.debug_level = kwargs.get("debug_level", 0)
        self.tz = kwargs.get("tz", "GMT")
        self.sql_create_table = kwargs.get("sql_create_table")
        self.sql_insert_table = kwargs.get("sql_insert_table")
        self.db_init(**kwargs)

    def db_init(self, **kwargs):
        '''
        TEMPLATE should be overwritten.
        - initialize your database.
        - the return value should be:
            + False: something error.
            + True: succeeded.
        '''
        return True

    def db_submit(self, **kwargs):
        '''
        TEMPLATE should be overwritten.
        - submit the data into your database such as mongodb or sqlite3.
        - the return value should be:
            + None: ignore parsing.
            + False: something error.
            + True: succeeded.
        '''
        return True

    """
    def get_app_data(self, kv_data, **kwargs):
        #if something error happenes, return False.
        app_data = kv_data.get("__app_data")
        if app_data is None:
            self.logger.error("the payload haven't been parsed.")
            return False
        app_data["ts"] = iso8601_to_fixed_ts(kv_data["Time"], self.tz)
        app_data["deveui"] = kv_data["DevEUI"]
        app_data["rssi"] = kv_data["LrrRSSI"]
        app_data["snr"] =  kv_data["LrrSNR"]
        if self.debug_level > 0:
            self.logger.debug("app_data = {}".format(app_data))
        return app_data
    """
