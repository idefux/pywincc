import adodbapi
import logging
import warnings
import re
from mssql import mssql, MsSQLException
from helper import datetime_to_str, utc_to_local_time
from alarm import Alarm, AlarmRecord

class WinCCException(Exception):
    def __init__(self, message=''):
        self.message = message   

class wincc(mssql):

    conn_str = "Provider=%(provider)s;Catalog=%(database)s;Data Source=%(host)s"
    provider = 'WinCCOLEDBProvider.1'

    def __init__(self, host, database=None):
        """Class constructor. If database is not given it tries to determine wincc database name by connecting with
        Microsoft OLEDB Provider first. You can save some time by passing database name here.
        """

        if not host.find('\WINCC'):
            host += '\WINCC'
            logging.info("Missing instance name at hostname. Appending \WINCC.")
        
        self.host = host
        self.database = database
        self.conn = None
        self.cursor = None


    def connect(self):
        """Connect to wincc mssql database using WinCCOLEDBProvider.1"""
        if not self.database:
            warnings.warn("Initial Database not given. Will try to fetch it's name. But this will take some time.")
            logging.info("Trying to fetch wincc database name")
            self.database = self.fetch_wincc_database_name()

        if not self.database:
            raise WinCCException("Could not fetch WinCC runtime database. Please check databases at host {host}.".format(host=self.host))

        try:
            logging.info("Trying to connect to {host} database {host}".format(host=self.host, database=self.database))
            self.conn = adodbapi.connect(self.conn_str, provider=self.provider, host=self.host, database=self.database)
            self.cursor = self.conn.cursor()
            #print("Connected to database.")

        except adodbapi.DatabaseError or adodbapi.InterfaceError:
            raise WinCCException(message='Connection to host {host} failed.'.format(host=self.host))


    def filter_wincc_runtime_database(self, databases):
        """Receives a list of databases as input and extracts wincc runtime databases
        
        Examples:
        >>> dbs = [u'CC_OS_1__15_01_08_16_40_41', \
        u'CC_OS_1__15_01_08_16_40_41R', \
        u'master', \
        u'VAS-AGROSCHW-PC_OS(1)_ALG_201504072200_201504081000']
        >>> w = wincc('localhost', 'xxx')
        >>> w.filter_wincc_runtime_database(dbs)
        u'CC_OS_1__15_01_08_16_40_41R'
        """
        r = re.compile(r"CC_OS_[\d_]+R$")
        wincc_runtime_databases = filter(r.match, databases)
        if len(wincc_runtime_databases) == 1:
            logging.debug("Using WinCC Runtime Database: {db}".format(db=wincc_runtime_databases[0]))
            return wincc_runtime_databases[0]
        elif len(wincc_runtime_databases) == 0:
            logging.warn("Could not find a WinCC runtime database.")
            return None
        if len(wincc_runtime_databases) > 1:
            logging.warn("Found more than 1 WinCC runtime databases. Check for possible dead links at host.")
            wincc_runtime_databases.sort()
            logging.warn("Returning newest database.")
            logging.debug("Using WinCC Runtime Database: {1}".format(wincc_runtime_databases[-1]))
            return wincc_runtime_databases[-1]

    def filter_wincc_config_database(self, databases):
        """Receives a list of databases as input and extracts wincc runtime databases
        
        Examples:
        >>> dbs = [u'CC_OS_1__15_01_08_16_40_41', \
        u'CC_OS_1__15_01_08_16_40_41R', \
        u'master', \
        u'VAS-AGROSCHW-PC_OS(1)_ALG_201504072200_201504081000']
        >>> w = wincc('localhost', 'xxx')
        >>> w.filter_wincc_config_database(dbs)
        u'CC_OS_1__15_01_08_16_40_41'
        """
        r = re.compile(r"CC_OS_[\d_]+$")
        wincc_config_databases = filter(r.match, databases)
        if len(wincc_config_databases) == 1:
            logging.debug("Using WinCC config Database: {db}".format(db=wincc_config_databases[0]))
            return wincc_config_databases[0]
        elif len(wincc_config_databases) == 0:
            logging.warn("Could not find a WinCC config database.")
            return None
        if len(wincc_config_databases) > 1:
            logging.warn("Found more than 1 WinCC config databases. Check for possible dead links at host.")
            wincc_config_databases.sort()
            logging.warn("Returning newest database.")
            logging.debug("Using WinCC config Database: {1}".format(wincc_config_databases[-1]))
            return wincc_config_databases[-1]
    
    def fetch_wincc_database_name(self):
        """Connect to MsSQL server with Microsoft SQLOLEDB.1 provider, get database list and filter wincc runtime database"""
        try:
            m = mssql(self.host, '')
            m.connect()
            databases = m.fetch_database_names()
            m.close()
            self.database = self.filter_wincc_runtime_database(databases)
            return self.database
            if not self.database:
                raise WinCCException("Could not fetch wincc runtime database. Please make sure WinCC runtime is active on host {host}".format(host=self.host))
        except MsSQLException:
            raise WinCCException("Could not connect to host {host} with Microsoft SQLOLEDB.1 provider".format(host=self.host))
            return None
        
    def fetch_wincc_config_database_name(self):
        """Connect to MsSQL server with Microsoft SQLOLEDB.1 provider, get database list and filter wincc runtime database"""
        try:
            mssql = mssql(self.host, '')
            mssql.connect()
            databases = mssql.fetch_database_names()
            mssql.close()
            return self.filter_wincc_config_database(databases)
        except MsSQLException:
            raise WinCCException("Could not connect to host {host} with Microsoft SQLOLEDB.1 provider".format(host=self.host))
            return None

    def execute(self, query):
        """Execute (T)SQL query. Connection to server must be establidhed in advance."""
        try:
            logging.debug("Executing query {query}.".format(query=query))
            self.cursor.execute(query)            
        except (adodbapi.DatabaseError, adodbapi.InterfaceError) as e:
            logging.error(str(e))
            raise WinCCException("query: '{query}' failed. Reason {reason}.".format(query=query, reason=str(e)))

    def print_alarms(self):
        """Print alarms to stdout"""
        logging.debug("wincc.print_alarms()")
        logging.debug("Rowcount: {rowcount}".format(rowcount=self.rowcount()))
        if self.rowcount():
            for rec in self.fetchall():
                print rec['MsgNr'], rec['State'], datetime_to_str(utc_to_local_time(rec['DateTime'])), rec['Classname'], rec['Typename'], rec['Text1']    
            print("Rows: {rows}".format(rows=self.rowcount()))
            
    def create_alarm_record(self):
        """Fetches alarms from cursor (after query) and returns an AlarmRecord object"""
        if self.rowcount():
            alarms = AlarmRecord()
            for rec in self.fetchall():
                alarms.add(Alarm(rec['MsgNr'], rec['State'], datetime_to_str(utc_to_local_time(rec['DateTime'])), rec['Classname'], rec['Typename'], rec['Text1']))
            return alarms
        return None
                
    def print_operator_messages(self):
        if self.rowcount():
            for rec in self.fetchall():
                print datetime_to_str(utc_to_local_time(rec['DateTime'])), rec['PText1'], rec['PText2'], rec['PText3'], rec['PText4'], rec['Username']

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            
if __name__ == "__main__":
    import doctest
    doctest.testmod()
