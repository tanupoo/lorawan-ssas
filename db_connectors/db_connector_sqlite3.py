from db_connector_template import db_connector_template
import sqlite3

class db_connector(db_connector_template):

    '''
    you can use the following code to submit data into the default
    sqlite3.

        from connector_sqlite3 import connector_sqlite3

        class handler(connector_sqlite3):
            pass

        p = handler(logger=self.logger, debug_level=self.debug_level,
                   db_name="your_database_name")
        p.submit(kv_data)
    '''
    def db_init(self, **kwargs):
        """
        this method will call self.create_db() even if it is not needed.
        """
        self.db_name = kwargs.get("db_name")
        if self.db_name is None:
            raise ValueError("db_name is required in the handler.")
        self.con = sqlite3.connect(self.db_name)
        self.cur = self.con.cursor()
        if self.cur is None:
            raise ValueError("cursor has not been opened.")
        self.sql_create_table = kwargs.get("sql_create_table")
        if self.sql_create_table is not None:
            # XXX need to check whether the table has existed.
            self.cur.execute(self.sql_create_table)
        return True

    def db_submit(self, kv_data, **kwargs):
        """
        this method will call self.make_insert_string().
        the value of make_insert_string method:
            None: ignore this data.
            (string): insert SQL
        """
        if self.cur is None:
            raise ValueError("sqlite3 is not connected.")
        app_data = self.get_app_data(kv_data, **kwargs)
        if app_data is False:
            return False
        self.cur.execute(self.insert_tab_sql, app_data)
        self.con.commit()
        if self.debug_level > 0:
            self.logger.debug("Succeeded submitting data into sqlite3.")
        return True

