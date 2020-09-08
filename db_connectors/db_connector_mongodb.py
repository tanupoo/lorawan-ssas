from db_connector_template import db_connector_template
from pymongo import MongoClient
import pymongo.errors

class db_connector(db_connector_template):

    '''
    e.g.
        from db_connector_mongodb import db_connector

        p = handler(logger=self.logger, debug_level=self.debug_level,
                   db_connect="parameter_for_connect")
        p.submit(kv_data)

    e.g. of <parameter_for_connect>
        host=127.0.0.1 port=5432 dbname=postgres user=demo password=demo1
    '''
    def db_init(self, **kwargs):
        """
        db_name: default is "lorawan".
        db_collection: default is "sensors".
        db_addr: default is "localhost".
        db_port: default is 27017.
        db_timeout: default is 2000. (2 sec)
        """
        self.db_name = kwargs.setdefault("db_name", "lorawan")
        self.db_col_name = kwargs.setdefault("db_collection", "sensors")
        self.db_addr = kwargs.setdefault("db_addr", "localhost")
        self.db_port = kwargs.setdefault("db_port", 27017)
        self.db_username = kwargs.setdefault("db_username", None)
        self.db_password = kwargs.setdefault("db_password", None)
        self.timeout = kwargs.setdefault("db_timeout", 2000)
        self.logger.info(f"""Connect MongoDB on {self.db_addr}:{self.db_port}
                         for {self.db_name}.{self.db_col_name}""")
        self.con = MongoClient(self.db_addr, self.db_port,
                               serverSelectionTimeoutMS=self.timeout,
                               username=self.db_username,
                               password=self.db_password)
        self.db = self.con[self.db_name]
        self.col = self.db[self.db_col_name]
        return True

    def db_submit(self, kv_data, **kwargs):
        try:
            self.col.insert_one(kv_data)
        except pymongo.errors.ServerSelectionTimeoutError as e:
            self.logger.error("timeout, mongodb looks not ready yet.")
            return False
        #
        self.logger.debug("Succeeded submitting data into MongoDB.")
        return True

