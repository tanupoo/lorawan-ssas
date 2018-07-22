# -*- coding: utf-8 -*-

from __future__ import print_function

from app_util import default_logger
'''
# if you use the default mongodb.
from parser_thru import parser as parser_thru
'''

class parser():

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

    def submit(self, kv_data, **kwargs):
        '''
        submit the data into a database such as mongodb or sqlite3.
        '''
        '''
        # you can use the following code to submit data into the default
        # mongodb.
        p = parser_thru(logger=self.logger, debug_level=self.debug_level)
        p.submit(kv_data)
        '''
        return True

