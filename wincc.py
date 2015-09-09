from __future__ import print_function
import adodbapi
import logging
import warnings
import re
import pickle
import traceback
import os

from mssql import mssql, MsSQLException
from helper import datetime_to_str, utc_to_local, tic, str_to_date,\
    daterange, date_to_str, datetime_to_str_without_ms
from alarm import Alarm, AlarmRecord, alarm_query_builder
from tag import Tag, TagRecord
from operator_messages import om_query_builder, OperatorMessageRecord,\
    OperatorMessage
from report import generate_alarms_report, operator_messages_report
from datetime import timedelta
from collections import namedtuple
import monkey_patch


class WinCCException(Exception):
    def __init__(self, message=''):
        # Call the base class constructor with the parameters it needs
        super(WinCCException, self).__init__(message)


class wincc(mssql):

    conn_str = "Provider=%(provider)s;Catalog=%(database)s;\
    Data Source=%(host)s"
    provider = 'WinCCOLEDBProvider.1'

    def __init__(self, host, database=None):
        """Class constructor. If database is not given it tries to determine \
        wincc database name by connecting with
        Microsoft OLEDB Provider first. You can save some time by passing \
        database name here.
        """

        if host.find(r'\WINCC') == -1:
            host += r'\WINCC'
            logging.info(r"Missing instance name at hostname. Appending\
             \WINCC.")

        self.host = host
        self.database = database
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to wincc mssql database using WinCCOLEDBProvider.1"""
        if not self.database:
            warnings.warn("Initial Database not given. Will try to fetch it's\
             name. But this will take some time.")
            logging.info("Trying to fetch wincc database name")
            self.database = self.fetch_wincc_database_name()

        if not self.database:
            raise WinCCException("Could not fetch WinCC runtime database. \
            Please check databases at host {host}.".format(host=self.host))

        try:
            logging.info("Trying to connect to %s database %s", self.host,
                         self.database)
            self.conn = adodbapi.connect(self.conn_str,
                                         provider=self.provider,
                                         host=self.host,
                                         database=self.database)
            self.cursor = self.conn.cursor()

        except (adodbapi.DatabaseError, adodbapi.InterfaceError) as e:
            print(e)
            print(traceback.format_exc())
            raise WinCCException(message='Connection to host {host} failed.'
                                 .format(host=self.host))

    def filter_wincc_runtime_database(self, databases):
        """Extract wincc runtime databases out of given databases

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
            logging.debug("Using WinCC Runtime Database: %s",
                          wincc_runtime_databases[0])
            return wincc_runtime_databases[0]
        elif len(wincc_runtime_databases) == 0:
            logging.warn("Could not find a WinCC runtime database.")
            return None
        if len(wincc_runtime_databases) > 1:
            logging.warn("Found more than 1 WinCC runtime databases. Check for \
            possible dead links at host.")
            wincc_runtime_databases.sort()
            logging.warn("Returning newest database.")
            logging.debug("Using WinCC Runtime Database: %s",
                          wincc_runtime_databases[-1])
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
            logging.debug("Using WinCC config Database: %s",
                          wincc_config_databases[0])
            return wincc_config_databases[0]
        elif len(wincc_config_databases) == 0:
            logging.warn("Could not find a WinCC config database.")
            return None
        if len(wincc_config_databases) > 1:
            logging.warn("Found more than 1 WinCC config databases. Check for"
                         " possible dead links at host.")
            wincc_config_databases.sort()
            logging.warn("Returning newest database.")
            logging.debug("Using WinCC config Database: %s",
                          wincc_config_databases[-1])
            return wincc_config_databases[-1]

    def fetch_wincc_database_name(self):
        """
        Connect to MsSQL server with Microsoft SQLOLEDB.1 provider.
        Get database list and filter wincc runtime databases.
        """
        try:
            m = mssql(self.host, '')
            m.connect()
            databases = m.fetch_database_names()
            m.close()
            self.database = self.filter_wincc_runtime_database(databases)
            if not self.database:
                raise WinCCException("Could not fetch wincc runtime database. "
                                     "Please make sure WinCC runtime is active"
                                     " on host {host}".format(host=self.host))
            return self.database
        except MsSQLException:
            raise WinCCException("Could not connect to host {host} with \
            Microsoft SQLOLEDB.1 provider".format(host=self.host))

    def fetch_wincc_config_database_name(self):
        """
        Connect to MsSQL server with Microsoft SQLOLEDB.1 provider.
        Get database list and filter wincc runtime database.
        """
        try:
            mssql_ = mssql(self.host, '')
            mssql_.connect()
            databases = mssql_.fetch_database_names()
            mssql_.close()
            return self.filter_wincc_config_database(databases)
        except MsSQLException:
            raise WinCCException("Could not connect to host {host} with \
            Microsoft SQLOLEDB.1 provider".format(host=self.host))

    def execute(self, query):
        """
        Execute (T)SQL query.
        Connection to server must be establidhed in advance.
        """
        try:
            logging.debug("Executing query %s.", query)
            self.cursor.execute(query)
        except (adodbapi.DatabaseError, adodbapi.InterfaceError) as e:
            errormsg = "Query: %s failed. Reason: %s.", query, str(e)
            logging.error(errormsg)
            raise WinCCException(errormsg)

    def print_alarms(self):
        """Print alarms to stdout"""
        logging.debug("wincc.print_alarms()")
        logging.debug("Rowcount: {rowcount}".format(rowcount=self.rowcount()))
        if self.rowcount():
            for rec in self.fetchall():
                datetime_local = utc_to_local(rec['DateTime'])
                datetime_str = datetime_to_str_without_ms(datetime_local)
                print(u"{rec[MsgNr]} {rec[State]:2} {datetime} {rec[Classname]}"
                      u" {rec[Typename]:9} {rec[Text2]:14} {rec[Text1]}"
                      .format(rec=rec, datetime=datetime_str))
            print("Rows: {rows}".format(rows=self.rowcount()))

    def create_alarm_record(self):
        """Fetches alarms from cursor and returns an AlarmRecord object"""
        if self.rowcount():
            alarms = AlarmRecord()
            for rec in self.fetchall():
                datetime = datetime_to_str(utc_to_local(rec['DateTime']))
                alarms.push(Alarm(rec['MsgNr'], rec['State'], datetime,
                                  rec['Classname'], rec['Typename'],
                                  rec['Text2'], rec['Text1']))
            return alarms
        return None

    def create_operator_messages_record(self):
        """
        Fetches operator messages from cursor.
        Return them as OperatorMessageRecord object"""
        if self.rowcount():
            operator_messages = OperatorMessageRecord()
            for rec in self.fetchall():
                datetime = datetime_to_str(utc_to_local(rec['DateTime']))
                op = OperatorMessage(datetime, rec['PText1'], rec['PText4'],
                                     rec['PText2'], rec['PText3'],
                                     rec['Username'])
                operator_messages.push(op)
            return operator_messages
        return None

    def create_tag_record(self):
        """Fetch tags from cursor and return a TagRecord object"""
        if self.rowcount():
            tags = TagRecord()
            for rec in self.fetchall():
                datetime = utc_to_local(rec['timestamp'])
                tags.push(Tag(datetime, rec['realvalue']))
            return tags
        return None

    def create_tag_records(self):
        """Fetch tags from cursor and return a TagRecord objects.
        This is experimental to test handling of multiple records in cursor.
        """
        tag_records = []
        p_rec = -1
        if self.rowcount():
            # Create first recordset
            tag_records.append(TagRecord())
            p_rec += 1
            rec = self.fetchone()
            tag_records[p_rec].tagid = rec['valueid']
            datetime = utc_to_local(rec['timestamp'])
            tag_records[p_rec].push(Tag(datetime, rec['realvalue']))

            for rec in self.fetchall():
                if rec['valueid'] != tag_records[p_rec].tagid:
                    tag_records.append(TagRecord())
                    p_rec += 1
                    tag_records[p_rec].tagid = rec['valueid']
                datetime = utc_to_local(rec['timestamp'])
                tag_records[p_rec].push(Tag(datetime, rec['realvalue']))
            return tag_records
        return None

    def print_operator_messages(self):
        if self.rowcount():
            for rec in self.fetchall():
                print("PText1", rec['PText1'])
                print("PText2", rec['PText2'])
                print("PText3", rec['PText3'])
                print("PText4", rec['PText4'])
                print(datetime_to_str(utc_to_local(rec['DateTime'])),
                      rec['PText1'], rec['PText2'], rec['PText3'],
                      rec['PText4'], rec['Username'])

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def do_alarm_report(begin_time, end_time, host, database='',
                    cache=False, use_cached=False, host_desc=''):
    if not use_cached:
        query = alarm_query_builder(begin_time, end_time, '', True, '')
        alarms = None
        toc = tic()
        try:
            w = wincc(host, database)
            w.connect()
            w.execute(query)
            # w.print_operator_messages()
            alarms = w.create_alarm_record()
            # print("Fetched data in {time}.".format(time=round(toc(),3)))
            if cache:
                print("Caching!")
                logging.debug("Writing alarms to %s", "alarms.pkl")
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
        logging.debug("Current dir: %s", os.getcwd())
        logging.debug("Loading alarms from file 'alarms.pkl'.")
        pkl_file = open('alarms.pkl', 'rb')
        alarms = pickle.load(pkl_file)
        pkl_file.close()

    generate_alarms_report(alarms, begin_time, end_time, host_desc, '')


def do_batch_alarm_report(begin_day, end_day, host_address, database,
                          host_desc='', timestep=1):
    dt_begin_day = str_to_date(begin_day)
    dt_end_day = str_to_date(end_day)

    for day in daterange(dt_begin_day, dt_end_day):
        logging.info('Trying to generate report for %s - %s.',
                     dt_begin_day, dt_end_day)
        do_alarm_report(date_to_str(day), date_to_str(day + timedelta(timestep)),
                        host_address, database, host_desc=host_desc)


def do_operator_messages_report(begin_time, end_time, host, database='',
                                cache=False, use_cached=False, host_desc=''):
    if not use_cached:
        query = om_query_builder(begin_time, end_time)
        operator_messages = None
        toc = tic()
        try:
            w = wincc(host, database)
            w.connect()
            w.execute(query)
            operator_messages = w.create_operator_messages_record()
            if cache:
                print("Caching!")
                logging.debug("Writing operator_messages to %s",
                              "operator_messages.pkl")
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
        logging.debug("Current dir: %s", os.getcwd())
        logging.debug("Loading operator_messages from file "
                      "'operator_messages.pkl'.")
        pkl_file = open('operator_messages.pkl', 'rb')
        operator_messages = pickle.load(pkl_file)
        pkl_file.close()

    print("Generating HTML output...")
    operator_messages_report(operator_messages, begin_time, end_time,
                             host_desc)


WinCCHost = namedtuple('WinCCHost',
                       'hostname host_address database descriptive_name')


class WinCCHosts():

    filename = './hosts.sav'

    def __iter__(self):
        return iter(self.hosts)

    def __init__(self):
        if self.load_from_file():
            pass
        else:
            self.hosts = []

    def load_from_file(self):
        try:
            logging.info("Trying to open file %s for loading stored hosts.",
                         self.filename)
            with open(self.filename, 'rb') as fh:
                self.hosts = pickle.load(fh)
                return True
        except IOError:
            logging.error("Opening file %s failed. Could not load hosts.",
                          self.filename)
            return False

    def save_to_file(self):
        try:
            logging.debug("Trying to open file %s for saving hosts.",
                          self.filename)
            with open(self.filename, 'wb') as fh:
                pickle.dump(self.hosts, fh)
                return True
        except IOError:
            logging.error("Opening file %s failed. Could not save hosts.",
                          self.filename)
            return False

    def add_host(self, hostname, host_address, database, descriptive_name):
        for host in self.hosts:
            if host.hostname.lower() == hostname.lower():
                raise KeyError('Hostname {0} already in list.'
                               .format(hostname))
        self.hosts.append(WinCCHost(hostname, host_address, database,
                                    descriptive_name))

    def remove_host(self, hostname):
        for host in self.hosts:
            if host.hostname.lower() == hostname.lower():
                self.hosts.remove(host)
                return True
        return False

    def get_host(self, hostname):
        """Return host details for given name.
        If not found in database, raise KeyError.
        """
        for host in self.hosts:
            if host.hostname.lower() == hostname.lower():
                return host
        raise KeyError("Hostname {0} not found in hosts database."
                       .format(hostname))


def get_host_by_name(hostname):
    hosts = WinCCHosts()
    return hosts.get_host(hostname)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
