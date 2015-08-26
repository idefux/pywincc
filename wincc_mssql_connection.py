import adodbapi
import re

from helper import utc_to_local_time, datetime_to_str

def adodbapi_SQLrow__unicode__(self):
    """Extend adodbapi's SQLrow class with an __unicod__ function.
    This is just a copy of the str method where I replaced the two occurences of 'str' by 'unicode'."""    
    return unicode(tuple(unicode(self._getValue(i)) for i in range(self.rows.numberOfColumns)))

def adodbapi_SQLrow__str__(self):
    """Overwrite adodbapi's SQLrow classes __str__ function to fix unicode errors when attempting to print it"""
    return unicode(self).encode('utf-8')

adodbapi.SQLrow.__unicode__ = adodbapi_SQLrow__unicode__
adodbapi.SQLrow.__str__ = adodbapi_SQLrow__str__

class WinCCException(Exception):
    def __init__(self, message=''):
        self.message = message        

class wincc_mssql_connection():
    conn_str_mssql = "Provider=%(provider)s; Integrated Security=SSPI; Persist Security Info=False; Initial Catalog=%(database)s;Data Source=%(host)s"
    conn_str_winccoledb = "Provider=%(provider)s;Catalog=%(database)s;Data Source=%(host)s"
    #host = r"10.1.57.50\WinCC"
    #host = r"10.0.0.172\WinCC"
    #host = default_host
    #database = "CC_OS_1__15_01_08_16_40_41"
    #initial_database = default_database
    provider = 'SQLOLEDB.1'
    provider_winccoledb = 'WinCCOLEDBProvider.1'
    current_database = ''
    connection_established = False
    connection_status_text = 'Not connected yet.'
    
    def __init__(self, host, database):
        self.host = host
        self.initial_database = database
        self.databases = []
        self.conn = False
        self.c = False
        self.conn_wincc = False
        self.c_wincc = False
     
    def connect(self):
        print("Connecting to remote host '{host}' and opening database '{database}'.".format(host=self.host, database=self.initial_database))
        try:
            self.conn = adodbapi.connect(self.conn_str_mssql, provider=self.provider, host=self.host, database=self.initial_database)
            self.c = self.conn.cursor()
            self.connection_established = True
            self.set_current_database()
            self.connection_status_text = 'Connection to host {host} established.'.format(host=self.host)
            print("Connected to database.")
        except Exception as e:
            print("Error when connecting to mssql host {host} and opening database {database}. Quitting...".format(host=self.host, database=self.initial_database))
            #print(e)
            self.connection_established = False
            raise WinCCException(message='Connection to host {host} failed.'.format(host=self.host))

    def connect_winccoledbprovider(self):
        print("Connecting to remote host '{host}' with provider '{provider}' and opening database '{database}'.".format(host=self.host, provider=self.provider_winccoledb, database=self.initial_database))
        try:
            self.conn_wincc = adodbapi.connect(self.conn_str_winccoledb, provider=self.provider_winccoledb, host=self.host, database=self.initial_database)
            self.c_wincc = self.conn_wincc.cursor()
            self.connection_established = True
            #self.set_current_database()
            self.connection_status_text = 'Connection to host {host} established.'.format(host=self.host)
            print("Connected to database.")
        except Exception as e:
            print("Error when connecting to mssql host {host} with provider '{provider}' and opening database {database}. Quitting...".format(host=self.host, provider=self.provider_winccoledb, database=self.initial_database))
            print(e)
            self.connection_established = False
            raise WinCCException(message='Connection to host {host} failed.'.format(host=self.host))

    def fetch_current_database_name(self):
        self.execute_cmd("SELECT DB_NAME();")
        self.current_database = self.c.fetchone()[0]
    
    def print_current_database_name(self):
        print("Database currently open: {database}".format(database = self.current_database))
    
    def set_current_database(self):
        self.current_database = self.fetch_current_database_name()
    
    def execute_cmd(self, cmd):
        try:
            self.c.execute(cmd)
            return 0
        except Exception as e:
            print("Execute of cmd {cmd} failed.".format(cmd=cmd))            
            print e
            return -1
    
    def execute_cmd_wincc(self, cmd):
        try:
            self.c_wincc.execute(cmd)
        except Exception as e:
            print("Execute of cmd {cmd} failed.".format(cmd=cmd))            
            print e
    
    def fetch_database_names(self):
        print("Fetching database names from host {host}".format(host=self.host))
        try:
            self.c.execute("EXEC sp_databases;")
            if self.c.rowcount > 0:
                for rec in self.c.fetchall():
                    self.databases.append(rec[0]) 
            else:
                self.c.execute("SELECT name FROM sys.databases")
                if self.c.rowcount > 0:
                    for rec in self.c.fetchall():
                        self.databases.append(rec[0])
        except Exception as e:
            print("Could not retrieve database list")
            print(e)
            
    def print_database_names(self):
        for db in self.databases:
            print(db)
    
    def print_table_names(self):
        print("Fetching table names from host '{host}' database '{database}'.".format(host=self.host, database=self.current_database))
        self.execute_cmd("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_NAME")
        for rec in self.c.fetchall():
            print rec         
        
    def close_connection(self):
        self.connection_established = False
        self.connection_status_text = 'Connection closed.'
        if self.c:
            self.c.close()
        if self.conn:
            self.conn.close()
        if self.c_wincc:
            self.c_wincc.close()
        if self.conn_wincc:
            self.conn_wincc.close()
        
    def select_wincc_config_database(self):
        r = re.compile(r"CC_OS_[\d_]+$")
        wincc_config_databases = filter(r.match, self.databases)
        if len(wincc_config_databases) == 1:
            self.wincc_config_database = wincc_config_databases[0]
            return 0
        if len(wincc_config_databases) == 0:
            print("Error: Could not find a WinCC configuration database")
            return -1
        if len(wincc_config_databases) > 1:
            print("Error: Found more than 1 WinCC configuration databases. Check and delete dead links.")
            return -1
        
    def select_wincc_runtime_database(self):
        r = re.compile(r"CC_OS_[\d_]+R$")
        wincc_runtime_databases = filter(r.match, self.databases)
        if len(wincc_runtime_databases) == 1:
            self.wincc_runtime_database = wincc_runtime_databases[0]
            return 0
        if len(wincc_runtime_databases) == 0:
            print("Error: Could not find a WinCC runtime database")
            return -1
        if len(wincc_runtime_databases) > 1:
            print("Error: Found more than 1 WinCC runtime databases. Check and delete dead links.")
            return -1
    
    def use_wincc_runtime_database(self):
        if not self.wincc_runtime_database:
            if self.select_wincc_runtime_database() != 0:
                print("Could not retrieve WinCC runtime database")
                return -1
            else:
                return self.execute_cmd("USE {db};".format(db=self.wincc_runtime_database))
        else:
            self.execute_cmd("USE {db};".format(db=self.wincc_runtime_database))                
                
    def use_wincc_config_database(self):
        if not self.wincc_config_database:
            if self.select_wincc_config_database() != 0:
                print("Could not retrieve WinCC configuration database")
                return -1
            else:
                return self.execute_cmd("USE {db};".format(db=self.wincc_config_database))                  
        else:
            self.execute_cmd("USE {db};".format(db=self.wincc_config_database))
            
    def fetch_alarms(self, begin_datetime, end_datetime=0, alarm_text=''):
        try:
            self.execute_cmd_wincc("ALARMVIEW:Select * FROM AlgViewDeu WHERE DateTime > '{begin}'".format(begin=begin_datetime))
        except Exception as e:
            print("Could not read alarms")
            print(e)
        
    def print_alarms(self):
        if self.c_wincc.rowcount > 0:
            for rec in self.c_wincc.fetchall():
                print rec['MsgNr'], rec['State'], datetime_to_str(utc_to_local_time(rec['DateTime'])), rec['Classname'], rec['Typename'], rec['Text1']
            print("Rows: {rows}".format(rows=self.c_wincc.rowcount))
            
    def fetch_operator_messages(self, begin_datetime, end_datetime=0, alarm_text=''):
        try:
            self.execute_cmd_wincc("ALARMVIEW:Select * FROM AlgViewDeu WHERE MsgNr = 12508141 AND DateTime > '{begin}'".format(begin=begin_datetime))
        except Exception as e:
            print("Could not read operator messages")
            print(e)            
            
    def print_operator_messages(self):
        if self.c_wincc.rowcount > 0:
            for rec in self.c_wincc.fetchall():
                print datetime_to_str(utc_to_local_time(rec['DateTime'])), rec['PText1'], rec['PText2'], rec['PText3'], rec['PText4'], rec['Username']
                        
    def get_tag_values(self, tag_id, begin_time, end_time='0000-00-00 00:00:00.000', timestep=0, mode='avg'):
        mode_dict = {'first': 1, 'last': 2, 'min': 3, 'max': 4, 'avg': 5, 'sum': 6, 'count':7,
                     'first_interpolated': 257, 'last_interpolated': 258, 'min_interpolated': 259, 'max_interpolated': 260, 
                     'avg_interpolated': 261, 'sum_interpolated': 262, 'count_interpolated': 263}
        
        mode_num = mode_dict[mode]
        
        try:
            if timestep == 0:
                self.execute_cmd_wincc("TAG:R,{tagid},'{begin_time}','{end_time}'".format(tagid=tag_id, begin_time=begin_time, end_time=end_time))
            else:
                self.execute_cmd_wincc("TAG:R,{tagid},'{begin_time}','{end_time}','TIMESTEP={timestep},{mode}'".format(tagid=tag_id, begin_time=begin_time, end_time=end_time, timestep=timestep, mode=mode_num))
        except Exception as e:
            print("Could not read TagLogging")
        
        if self.c_wincc.rowcount > 0:
            #print(type(self.c_wincc.fetchone()))
            return [[rec['DateTime'], rec['RealValue']] for rec in self.c_wincc.fetchall()]
        else:
            return []
            