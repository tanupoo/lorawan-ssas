# -*- coding: utf-8 -*-

from app_util import default_logger

class parser_template():

    @classmethod
    def parse(cls, hex_string):
        '''
        - parse the payload and return a Python dict object.
        - this method should be a class method so that it can be reused
          to just parse a hex string from other application.
        - the return value:
            + None: ignore parsing.
            + False: something error.
            + Others: a Python dict should be put in KEY_APP_DATA.
        '''
        return None

    def __init__(self, **kwargs):
        '''
        e.g. open a session to a database.
        kwargs should contain: logger, debug_level
        '''
        self.logger = kwargs.get("logger", default_logger)
        self.debug_level = kwargs.get("debug_level", 0)
        self.tz = kwargs.get("tz", "GMT")
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

