# -*- coding: utf-8 -*-

import sys
import psycopg2
from handler_template import handler_template
from app_util import iso8601_to_fixed_ts

class connector_postgres(handler_template):

    '''
    e.g.
        from connector_postgres import connector_postgres

        class handler(connector_postgres):
            pass

        p = handler(logger=self.logger, debug_level=self.debug_level,
                   db_connect="parameter_for_connect")
        p.submit(kv_data)

    e.g. of <parameter_for_connect>
        host=127.0.0.1 port=5432 dbname=postgres user=demo password=demo1
    '''
    def db_init(self, **kwargs):
        '''
        db_connect is mandate.
        tab_name is optional. A child class has to be defined.
        '''
        db_connect = kwargs.get("db_connect")
        if db_connect is None:
            raise ValueError("db_connect is required in the handler.")
        self.db_connect = db_connect
        self.tab_name = kwargs.get("tab_name")
        self.cur = None
        if self.db_connect is not None:
            self.con = psycopg2.connect(self.db_connect)
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
            raise ValueError("postgres is not ready.")
        return self.insert_db(kv_data, **kwargs)

    def fix_ts(self, ts):
        return iso8601_to_fixed_ts(ts, self.tz)
