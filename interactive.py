import shlex
import traceback
import time
from wincc_mssql_connection import wincc_mssql_connection, WinCCException
from alarm import query_builder

def alarms_cmd(wincc, args):
    """Parse alarm args and call wincc.fetch_alarms() method"""
    
    if len(args) < 1:
        print("Unsufficient arguments")
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
    
    query = query_builder(begin_time, end_time, msg_text, True, state)
    
    try:
        wincc.execute_cmd_wincc(query)
        wincc.print_alarms() 
    except Exception as e:
        print(e)
        print(traceback.format_exc())     
    

def interactive_mode_wincc(host, database):
    """Provides a shell for the user to interactively query the SQL server"""
    #special_user_commands = ['help', 'exit', 'databases', 'tables', 'database']
    help_text =  """Interactive mode with WinCCOLEDBProvider.1
exit:        Disconnect from server and quit program    
help:        Print this help text
tables:        Print table names of current databases
databases:    Print database names
database:        Print currently opened database
alarms:        Usage: alarms begin_time [end_time [text [state]]]
    """
    exit_message = "Disconnecting from server. Quitting interactive mode. Bye!"
    special_commands = {
                        'help': 'print(help_text)',
                        'exit': 'print(exit_message)\nloop=False',
                        'databases': 'wincc.fetch_database_names()\nwincc.print_database_names()',
                        'tables': 'wincc.print_table_names()',
                        'database': 'wincc.fetch_current_database_name()\nwincc.print_current_database_name()',
                        #'alarms': 'wincc.fetch_alarms(user_input.split(" ")[1])\nwincc.print_alarms()',
                        'alarms': 'alarms_cmd(wincc, user_input_args)',
                        'operator_messages': 'wincc.fetch_operator_messages(user_input.split(" ")[1])\nwincc.print_operator_messages()'
                        }
    
    # establish server connection
    try:
        wincc = wincc_mssql_connection(host, database)
        wincc.connect_winccoledbprovider()

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
                    wincc.execute_cmd_wincc(user_input)
                    if wincc.c_wincc.rowcount > 0:
                        for rec in wincc.c_wincc.fetchall():
                            print(unicode(rec))                    
                else:
                    print("exec: " + special_commands[user_input_cmd])
                    exec(special_commands[user_input_cmd])
                time_elapsed = time.time() - time_start
                print("Fetched data in {time}.".format(time=round(time_elapsed, 3)))
            except Exception as e:
                print(e)
                print(traceback.format_exc())        
    except WinCCException as e:
        print('Connection to host failed. Quitting program. Bye.')    
    finally:    # disconnect
        wincc.close_connection()