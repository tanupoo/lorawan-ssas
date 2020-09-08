from db_connector_template import db_connector_template
import psycopg2

class db_connector(db_connector_template):

    '''
    e.g.
        from db_postgres import db_connector

        class handler(connector_postgres):
            pass

        p = handler(logger=self.logger, debug_level=self.debug_level,
                   db_connect="parameter_for_connect")
        p.submit(kv_data)

    e.g. of <parameter_for_connect>
        host=127.0.0.1 port=5432 dbname=postgres user=demo password=demo1
    '''
    def db_init(self, **kwargs):
        """
        db_connect is mandate.
        """
        self.db_connect = kwargs.get("db_connect")
        if self.db_connect is None:
            raise ValueError("db_connect is required in the handler.")
        self.con = psycopg2.connect(self.db_connect)
        self.cur = self.con.cursor()
        if self.cur is None:
            raise ValueError("cursor has not been opened.")
        self.sql_create_table = kwargs.get("sql_create_table")
        if self.sql_create_table is not None:
            k = self.cur.execute(self.sql_create_table)
            self.con.commit()
        return True

    def db_submit(self, kv_data, **kwargs):
        """
        this method will call self.make_insert_string().
        the value of make_insert_string method:
            None: ignore this data.
            (string): insert SQL
        """
        if self.cur is None:
            raise ValueError("postgres is not ready.")
        if kv_data is False:
            return False
        if self.sql_insert_table is None:
            self.logger.error("sql_insert_table is not defined.")
            return False
        self.cur.execute(self.sql_insert_table, kv_data)
        self.con.commit()
        if self.debug_level > 0:
            self.logger.debug("Succeeded submitting data into postgress.")
        return True

