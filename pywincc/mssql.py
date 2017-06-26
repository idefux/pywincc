import adodbapi
import logging
import os

from .parameter import ParameterRecord, Parameter
import monkey_patch


class MsSQLException(Exception):
    def __init__(self, message=''):
        self.message = message


class mssql():
    conn_str = "Provider=%(provider)s; Integrated Security=SSPI; \
    Persist Security Info=False; Initial Catalog=%(database)s;\
    Data Source=%(host)s"
    provider = 'SQLOLEDB.1'

    def __init__(self, host, database=None):
        self.host = host
        self.database = database
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to mssql server using SQLOLEDB.1"""

        try:
            logging.info("Trying to connect to %s database %s", self.host,
                         self.database)
            # Python looses it's current working dir in the next instruction
            # Reset after connect
            curr_dir = os.getcwd()
            self.conn = adodbapi.connect(self.conn_str,
                                         provider=self.provider,
                                         host=self.host,
                                         database=self.database)
            os.chdir(curr_dir)
            self.cursor = self.conn.cursor()

        except (adodbapi.DatabaseError, adodbapi.InterfaceError) as e:
            logging.error(str(e))
            raise MsSQLException(message='Connection to host {host} failed.'
                                 .format(host=self.host))

    def execute(self, query):
        """Execute (T)SQL query.
        Connection to server must be established in advance.
        """
        try:
            logging.debug("Executing query {query}.".format(query=query))
            self.cursor.execute(query)
        except (adodbapi.DatabaseError, adodbapi.InterfaceError) as e:
            logging.error(str(e))
            raise MsSQLException("query: '{query}' failed. Reason {reason}."
                                 .format(query=query, reason=str(e)))

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def rowcount(self):
        return self.cursor.rowcount

    def fetch_database_names(self):
        logging.info("Fetching database names from host {host}"
                     .format(host=self.host))
        self.execute("EXEC sp_databases;")
        if self.rowcount():
            return [rec[0] for rec in self.fetchall()]
        else:
            logging.info("Server does not support 'EXEC sp_databases' stored \
            procedure. Trying 'SELECT name from sys.databases'.")
            self.execute("SELECT name FROM sys.databases")
            if self.rowcount():
                return [rec[0] for rec in self.fetchall()]
            else:
                return None

    def fetch_current_database_name(self):
        self.execute("SELECT DB_NAME();")
        return self.fetchone()[0]

    def fetch_table_names(self):
        logging.info("Trying to fetch table names.")
        self.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER \
        BY TABLE_NAME")
        if self.rowcount():
            return [rec[0] for rec in self.fetchall()]
        return None

    def create_parameter_record(self, filter_tag='', filter_name=''):
        """This is VAS only.
        It will not unless you have a parameter system same like ours.
        """
        query = "SELECT * FROM SYS_TABLE_P"
        if filter_tag and filter_name:
            query += " WHERE Tag LIKE '%{0}% AND \
            ucText LIKE '%{1}%'".format(filter_tag, filter_name)
        elif filter_tag:
            query += " WHERE Tag LIKE '%{0}%'".format(filter_tag)
        elif filter_name:
            query += " WHERE ucText LIKE '%{0}%'".format(filter_name)
        query += " ORDER BY PID;"
        logging.debug("Query: %s", query)
        self.execute(query)
        if self.rowcount():
            logging.debug("Found %s matching parameters", self.rowcount())
            params = ParameterRecord()
            for rec in self.fetchall():
                params.push(Parameter(rec['ID'], rec['TEXTID'], rec['HELPID'],
                                      rec['SPSID'], rec['PID'], rec['Tag'],
                                      rec['ucText'], rec['siValue'],
                                      rec['siMin'], rec['siMax'], rec['siDef'],
                                      rec['uiMul'], rec['ucRight'],
                                      rec['ucSection'], rec['ucGroup'],
                                      rec['ucUnit'], rec['ucHelpText']))
            return params
        else:
            return None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
