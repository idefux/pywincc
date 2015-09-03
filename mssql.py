import adodbapi
import logging

from parameter import ParameterRecord, Parameter

class MsSQLException(Exception):
    def __init__(self, message=''):
        self.message = message   

class mssql():
    conn_str = "Provider=%(provider)s; Integrated Security=SSPI; Persist Security Info=False; Initial Catalog=%(database)s;Data Source=%(host)s"
    provider = 'SQLOLEDB.1'

    def __init__(self, host, database=None):        
        
        self.host = host
        self.database = database
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to mssql server using SQLOLEDB.1"""

        try:
            logging.info("Trying to connect to host {host} database {db}".format(host=self.host, db=self.database))
            self.conn = adodbapi.connect(self.conn_str, provider=self.provider, host=self.host, database=self.database)
            self.cursor = self.conn.cursor()
            #print("Connected to database.")

        except (adodbapi.DatabaseError, adodbapi.InterfaceError) as e:
            logging.error(str(e))
            raise MsSQLException(message='Connection to host {host} failed.'.format(host=self.host))

    def execute(self, query):
        """Execute (T)SQL query. Connection to server must be establidhed in advance."""
        try:
            logging.debug("Executing query {query}.".format(query=query))
            self.cursor.execute(query)            
        except (adodbapi.DatabaseError, adodbapi.InterfaceError) as e:
            logging.error(str(e))
            raise MsSQLException("query: '{query}' failed. Reason {reason}.".format(query=query, reason=str(e)))

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def rowcount(self):
        return self.cursor.rowcount

    def fetch_database_names(self):
        logging.info("Fetching database names from host {host}".format(host=self.host))
        self.execute("EXEC sp_databases;")            
        if self.rowcount():
            return [rec[0] for rec in self.fetchall()]
        else:
            logging.info("Server does not support 'EXEC sp_databases' stored procedure. Trying 'SELECT name from sys.databases'.")
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
        self.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_NAME")
        if self.rowcount():
            return [rec[0] for rec in self.fetchall()]
        return None

    def create_parameter_record(self):
        """This is VAS only.
        It will not unless you have a parameter system same like ours.
        """
        query = "SELECT * FROM SYS_TABLE_P ORDER BY PID;"
        self.execute(query)
        if self.rowcount():
            params = ParameterRecord()
            for rec in self.fetchall():
                params.push(Parameter(rec['PID'], rec['Tag'], rec['ucText'],
                                      rec['siValue'], rec['siMin'],
                                      rec['siMax'], rec['siDef'],
                                      rec['ucSection'], rec['ucGroup'],
                                      rec['ucRight']))
            return params
        else:
            return None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


# This here is ugly, I know. But i need to have a __unicode__ method in adodbapi.SQLrow
# begin_ugly
def adodbapi_SQLrow__unicode__(self):
    """Extend adodbapi's SQLrow class with an __unicod__ function.
    This is just a copy of the str method where I replaced the two occurences of 'str' by 'unicode'."""    
    return unicode(tuple(unicode(self._getValue(i)) for i in range(self.rows.numberOfColumns)))

def adodbapi_SQLrow__str__(self):
    """Overwrite adodbapi's SQLrow classes __str__ function to fix unicode errors when attempting to print it"""
    return unicode(self).encode('utf-8')

adodbapi.SQLrow.__unicode__ = adodbapi_SQLrow__unicode__
adodbapi.SQLrow.__str__ = adodbapi_SQLrow__str__
# end_ugly

if __name__ == "__main__":
    import doctest
    doctest.testmod()
