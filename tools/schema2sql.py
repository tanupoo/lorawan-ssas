import sys
import re

"""
## sampe_table

The above definition will go into the below:

"sql_create_table": "create table if not exists sample_table ( ts timestamptz, deveui text, rssi float4, snr float4, batt int2)",
"sql_insert_table": "insert into sample_table ( ts, deveui, rssi, snr, batt) values ( %(ts)s, %(deveui)s, %(rssi)s, %(snr)s)"

below four columns are always created.

	ts timestamptz
	deveui text
	rssi float4
	snr float4
"""

re_title = re.compile("^##\s*(?P<title>[\w\d]+)\s*")
re_col = re.compile("^\s*(?P<col_name>[\w\d+]+)\s+(?P<col_type>[\w\d+]+)\s*")

class Schema():
    def __init__(self):
        self.table_name = None
        self.cols = []
    def add_table(self, name):
        self.table_name = name
    def add_col(self, name, col_type):
        self.cols.append((name, col_type))
    def flush(self):
        self.add_col("ts", "timestamptz")
        self.add_col("deveui", "text")
        self.add_col("rssi", "float4")
        self.add_col("snr", "float4")
        if self.table_name is None:
            raise ValueError("ERROR: table name is not defined.")
        statement = f"## {self.table_name}\n\n"
        statement += '"sql_create_table": '
        statement += f'"create table if not exists {self.table_name} ('
        statement += ", ".join([f'{n} {s}' for n,s in self.cols])
        statement += ')",\n\n'
        statement += '"sql_insert_table": '
        statement += f'"insert into {self.table_name} ('
        statement += ", ".join([f'{n}' for n,s in self.cols])
        statement += ') values ('
        statement += ", ".join([f'%({n})s' for n,s in self.cols])
        statement += ')"\n\n'
        return statement

with open(sys.argv[1]) as fd:
    tab = None
    for line in fd.readlines():
        r = re_title.match(line)
        if r:
            if tab is not None:
                print(tab.flush())
            tab = Schema()
            tab.add_table(r.group("title"))
            continue
        r = re_col.match(line)
        if r:
            tab.add_col(r.group("col_name"), r.group("col_type"))

    if tab is not None:
        print(tab.flush())
