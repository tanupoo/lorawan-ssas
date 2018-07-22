# -*- coding: utf-8 -*-

import sys
import sqlite3
import re
from handler_template import handler_template
from app_util import iso8601_to_fixed_ts

class connector_sqlite3(handler_template):

    '''
    you can use the following code to submit data into the default
    sqlite3.

        from connector_sqlite3 import connector_sqlite3

        class parser(connector_sqlite3):
            pass

        p = parser(logger=self.logger, debug_level=self.debug_level,
                   db_name="your_database_name")
        p.submit(kv_data)
    '''
    def db_init(self, **kwargs):
        '''
        this method will call self.create_db() even if it is not needed.
        '''
        db_name = kwargs.get("db_name")
        if db_name is None:
            raise ValueError("db_name is required in the handler.")
        self.db_name = db_name
        self.cur = None
        if self.db_name is not None:
            self.con = sqlite3.connect(self.db_name)
            self.cur = self.con.cursor()
        if self.cur is None:
            raise ValueError("cursor has not been opened.")
        #
        return self.create_db(**kwargs)

    def db_submit(self, kv_data, **kwargs):
        '''
        this method will call self.make_insert_string().
        the value of make_insert_string method:
            None: ignore this data.
            (string): insert SQL
        '''
        if self.cur is None:
            raise ValueError("{} is not connected.".format(self.db_name))
        return self.insert_db(kv_data, **kwargs)

    def fix_ts(self, ts):
        return iso8601_to_fixed_ts(ts, self.tz)
