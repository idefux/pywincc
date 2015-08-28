import adodbapi
import logging
import warnings
import re
import pickle
import traceback
import os

from mssql import mssql, MsSQLException
from helper import datetime_to_str, utc_to_local_time, tic, str_to_date,\
    daterange, date_to_str
from alarm import Alarm, AlarmRecord, alarm_query_builder
from operator_messages import om_query_builder, OperatorMessageRecord,\
    OperatorMessage
from report import alarms_report, operator_messages_report
from datetime import timedelta


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

        if host.find('\WINCC') == -1:
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
            logging.info("Trying to connect to {host} database {database}".format(host=self.host, database=self.database))
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
            errormsg = "query: '{query}' failed. Reason {reason}.".format(query=query, reason=str(e))
            logging.error(errormsg)            
            raise WinCCException(errormsg)

    def print_alarms(self):
        """Print alarms to stdout"""
        logging.debug("wincc.print_alarms()")
        logging.debug("Rowcount: {rowcount}".format(rowcount=self.rowcount()))
        if self.rowcount():
            for rec in self.fetchall():
                print rec['MsgNr'], rec['State'], datetime_to_str(utc_to_local_time(rec['DateTime'])), rec['Classname'], rec['Typename'], rec['Text2'], rec['Text1']    
            print("Rows: {rows}".format(rows=self.rowcount()))
            
    def create_alarm_record(self):
        """Fetches alarms from cursor and returns an AlarmRecord object"""
        if self.rowcount():
            alarms = AlarmRecord()
            for rec in self.fetchall():
                alarms.push(Alarm(rec['MsgNr'], rec['State'], datetime_to_str(utc_to_local_time(rec['DateTime'])), rec['Classname'], rec['Typename'], rec['Text2'], rec['Text1']))
            return alarms
        return None

    def create_operator_messages_record(self):
        """Fetches operator messages from cursor and returns an OperatorMessageRecord object"""
        if self.rowcount():
            operator_messages = OperatorMessageRecord()
            for rec in self.fetchall():
                operator_messages.push(OperatorMessage(datetime_to_str(utc_to_local_time(rec['DateTime'])), rec['PText1'], rec['PText4'], rec['PText2'], rec['PText3'], rec['Username']))
            return operator_messages
        return None

    def print_operator_messages(self):
        if self.rowcount():
            for rec in self.fetchall():
                print "PText1", rec['PText1']
                print "PText2", rec['PText2']
                print "PText3", rec['PText3']
                print "PText4", rec['PText4']
                print datetime_to_str(utc_to_local_time(rec['DateTime'])), rec['PText1'], rec['PText2'], rec['PText3'], rec['PText4'], rec['Username']

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def do_alarm_report(begin_time, end_time, host, database='', cache=False, use_cached=False):
    if not use_cached:
        query = alarm_query_builder(begin_time, end_time, '', True, '')
        alarms = None
        toc = tic()
        try:
            w = wincc(host, database)
            w.connect()
            w.execute(query)
            #w.print_operator_messages()
            alarms = w.create_alarm_record()
            #print("Fetched data in {time}.".format(time=round(toc(),3))) 
            if cache:
                print("Caching!")
                logging.debug("Writing alarms to {file}".format(file='alarms.pkl'))
                pkl_file = open('alarms.pkl', 'wb')
                pickle.dump(alarms, pkl_file)
                pkl_file.close()
        except WinCCException as e:
            print(e)
            print(traceback.format_exc())
        finally:
            w.close()
            exec_time_alarms = toc()
            print(exec_time_alarms) 
    else:
        logging.debug("Current dir: {0}".format(os.getcwd()))
        logging.debug("Loading alarms from file 'alarms.pkl'.")
        pkl_file = open('alarms.pkl', 'rb')
        alarms = pickle.load(pkl_file)
        pkl_file.close()
        
    #===========================================================================
    # if alarms:
    #     print(alarms)
    #     print(alarms.count())
    #     print(alarms.count_warning())
    #     print(alarms.count_error_day())
    #     print(alarms.count_error_now())
    #     print(alarms.count_stop_all())
    # else:
    #     print("No alarms found.")
    #===========================================================================    
    
    print("Generating HTML output...")
    alarms_report(alarms, begin_time, end_time, 'AGRO ENERGIE Schwyz')
    
def do_batch_alarm_report(begin_day, end_day, host, database):
    dt_begin_day = str_to_date(begin_day)
    dt_end_day = str_to_date(end_day)
    
    for day in daterange(dt_begin_day, dt_end_day):
        do_alarm_report(date_to_str(day), date_to_str(day + timedelta(1)), host, database)
    

def do_operator_messages_report(begin_time, end_time, host, database='', cache=False, use_cached=False):
    if not use_cached:
        query = om_query_builder(begin_time, end_time)
        operator_messages = None
        toc = tic()
        try:
            w = wincc(host, database)
            w.connect()
            w.execute(query)
            #w.print_operator_messages()
            operator_messages = w.create_operator_messages_record()
            #print("Fetched data in {time}.".format(time=round(toc(),3))) 
            if cache:
                print("Caching!")
                logging.debug("Writing operator_messages to {file}".format(file='operator_messages.pkl'))
                pkl_file = open('operator_messages.pkl', 'wb')
                pickle.dump(operator_messages, pkl_file)
                pkl_file.close()
        except WinCCException as e:
            print(e)
            print(traceback.format_exc())
        finally:
            w.close()
            exec_time_operator_messages = toc()
            print(exec_time_operator_messages) 
    else:
        logging.debug("Current dir: {0}".format(os.getcwd()))
        logging.debug("Loading operator_messages from file 'operator_messages.pkl'.")
        pkl_file = open('operator_messages.pkl', 'rb')
        operator_messages = pickle.load(pkl_file)
        pkl_file.close() 

    print("Generating HTML output...")
    operator_messages_report(operator_messages, begin_time, end_time, 'AGRO ENERGIE Schwyz')


if __name__ == "__main__":
    import doctest
    doctest.testmod()
