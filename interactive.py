import shlex
import traceback
import time
#from wincc_mssql_connection import wincc_mssql_connection, WinCCException
from wincc import wincc, WinCCException
from mssql import mssql, MsSQLException
from alarm import alarm_query_builder
from operator_messages import om_query_builder


class InteractiveModeWinCC():
    def __init__(self, host, database=''):
        self.wincc = wincc(host, database)
    
    def do_alarms(self, args):
        """Parse alarm args and call wincc.fetch_alarms() method"""
    
        if len(args) < 1:
            print("Insufficient arguments")
            return
    
        begin_time = args[0]
    
        if len(args) >= 2:
            end_time = args[1]
        else:
            end_time = ''
    
        if len(args) >= 3:
            msg_text = args[2]
        else:
            msg_text = ''
    
        if len(args) >= 4:
            state = args[3]
        else:
            state = ''
    
        query = alarm_query_builder(begin_time, end_time, msg_text, False, state)
    
        try:
            self.wincc.execute(query)
            self.wincc.print_alarms()
        except Exception as e:
            print(e)
            print(traceback.format_exc())     
    
    def do_operator_messages(self, args):
        """Parse operator message args and call wincc.fetch_operator_messages() method"""
    
        if len(args) < 1:
            print("Insufficient arguments")
            return
    
        begin_time = args[0]
    
        if len(args) >= 2:
            end_time = args[1]
        else:
            end_time = ''
    
        if len(args) >= 3:
            msg_text = args[2]
        else:
            msg_text = ''
    
        query = om_query_builder(begin_time, end_time, msg_text, False) 
    
        try:
            self.wincc.execute(query)
            self.wincc.print_operator_messages() 
        except Exception as e:
            print(e)
            print(traceback.format_exc())
    
    
    def run(self):
        """Provides a shell for the user to interactively query the SQL server"""
        #special_user_commands = ['help', 'exit', 'databases', 'tables', 'database']
        help_text = """Interactive mode with WinCCOLEDBProvider.1
    exit:        Disconnect from server and quit program    
    help:        Print this help text
    tables:        Print table names of current databases
    databases:    Print database names
    database:        Print currently opened database
    alarms:        Usage: alarms begin_time [end_time [text [state]]]
    operator_messages:    Usage: operator_messages begin_time [end_time [text]]
        """
        exit_message = "Disconnecting from server. Quitting interactive mode. Bye!"
        special_commands = {
                            'help': 'print(help_text)',
                            'exit': 'print(exit_message)\nloop=False',
                            #'databases': 'wincc.fetch_database_names()\nwincc.print_database_names()',
                            #'tables': 'wincc.print_table_names()',
                            #'database': 'wincc.fetch_current_database_name()\nwincc.print_current_database_name()',
                            #'alarms': 'wincc.fetch_alarms(user_input.split(" ")[1])\nwincc.print_alarms()',
                            'alarms': 'self.do_alarms(user_input_args)',
                            #'operator_messages': 'wincc.fetch_operator_messages(user_input.split(" ")[1])\nwincc.print_operator_messages()'
                            'operator_messages': 'self.do_operator_messages(user_input_args)'
                            }
    
        # establish server connection
        try:
            self.wincc.connect()
    
            # fire SQL queries until user stops
            loop = True
            while loop:
                try:
                    user_input = raw_input('Enter SQL command: ')     
                    #user_input_cmd = user_input.split(" ")[0]
                    args = shlex.split(user_input)
                    user_input_cmd = args[0]
                    user_input_args = args[1:]
                    time_start = time.time()
                    if user_input_cmd == 'tag':
                        print("Not implemented yet")
                    elif user_input_cmd not in special_commands:   
                        self.wincc.execute(user_input)
                        if self.wincc.rowcount():
                            for rec in self.wincc.fetchall():
                                print(unicode(rec))
                            print(self.wincc.rowcount())
                    else:
                        #print("exec: " + special_commands[user_input_cmd])
                        exec(special_commands[user_input_cmd])
                    time_elapsed = time.time() - time_start
                    print("Fetched data in {time}.".format(time=round(time_elapsed, 3)))
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())
    
        except WinCCException as e:
            print('Connection to host failed. Quitting program. Bye.')
        finally:    # disconnect
            self.wincc.close()

class InteractiveMode():
    def __init__(self, host, database=''):
        self.mssql = mssql(host, database)   
    
    def run(self):
        """Provides a shell for the user to interactively query the SQL server"""
        #special_user_commands = ['help', 'exit', 'databases', 'tables', 'database']
        help_text =  """exit:        Disconnect from server and quit program    
    help:        Print this help text
    tables:        Print table names of current databases
    databases:    Print database names
    database:        Print currently opened database
        """
        exit_message = "Disconnecting from server. Quitting interactive mode. Bye!"
        special_commands = {
                            'help': 'print(help_text)',
                            'exit': 'print(exit_message)\nloop=False',
                            'databases': 'print(self.m.fetch_database_names())',
                            'tables': 'print(self.mssql.fetch_table_names())',
                            'database': 'print(self.mssql.fetch_current_database_name())'
                            }
        
        # establish server connection
        try:
            self.mssql.connect()
    
            # fire SQL queries until user stops
            loop = True
            while loop:
                try:
                    user_command = raw_input('Enter SQL command: ')
                    if user_command not in special_commands:
                        self.mssql.execute(user_command)
                        if self.mssql.rowcount():
                            for rec in self.mssql.fetchall():
                                print(unicode(rec))
                            print(self.mssql.rowcount())
                    else:
                        exec(special_commands[user_command])
                except Exception as e:
                    print(e)        
        except MsSQLException as e:
            print('Connection to host failed. Quitting program. Bye.')    
        finally:    # disconnect
            self.mssql.close()   