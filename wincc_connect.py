import click
import time
import traceback

from wincc_mssql_connection import wincc_mssql_connection, WinCCException
import tag as wincc_tag
import alarm as wincc_alarm

from helper import local_time_to_utc, datetime_to_str
from tag import print_tag_logging

class StringCP1252ParamType(click.ParamType):
    """String Param Type for click to curb with annoying windows cmd shell encoding problems.
    German Umlaute are not correctly read from cmd line if Parameter Type is click.String"""
    name = 'text'

    def convert(self, value, param, ctx):
        if isinstance(value, bytes):
            enc = 'cp1252'
            value = value.decode(enc)            
            return value
        return value

    def __repr__(self):
        return 'STRING_CP1252'

STRING_CP1252 = StringCP1252ParamType()

@click.group()
#@click.option('--host', default='127.0.0.1', help='Hostname')
#@click.option('--database', default='', help='Initial Database (Catalog).')
#@click.option('--interactive', default=False, is_flag=True, help='Interactive mode. Fire queries manually.')
#@click.option('--tables', default=False, is_flag=True, help='List table names in given database.')
@click.option('--debug', default=False, is_flag=True, help='Turn on debug mode. Will print some debug messages.')
#@click.option('--wincc-provider', '-w', default=False, is_flag=True, help='Use WinCCOLEDBProvider.1 instead of SQLOLEDB.1')
def cli(debug):
    if debug:
        print("Debug mode not implemented yet.")
        #print('host: ' + host)
        #print('database: ' + database)
        #print('interactive: ' + str(interactive))
        #print('tables: ' + str(tables))
        #print('wincc-provider: ' + str(wincc_provider))
        

@cli.command()
@click.option('--host', '-h', default='127.0.0.1', help='Hostname')
@click.option('--database', '-d', default='', help='Initial Database (Catalog).')    
@click.option('--wincc-provider', '-w', default=False, is_flag=True, help='Use WinCCOLEDBProvider.1 instead of SQLOLEDB.1')
def interactive(host, database, wincc_provider):
    if wincc_provider:
        interactive_mode_wincc(host, database)
    else:
        interactive_mode_oledb(host, database)

def interactive_mode_oledb(host, database):
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
                        'databases': 'wincc.fetch_database_names()\nwincc.print_database_names()',
                        'tables': 'wincc.print_table_names()',
                        'database': 'wincc.fetch_current_database_name()\nwincc.print_current_database_name()'
                        }
    
    # establish server connection
    try:
        wincc = wincc_mssql_connection(host, database)
        wincc.connect()

        # fire SQL queries until user stops
        loop = True
        while loop:
            try:
                user_command = raw_input('Enter SQL command: ')
                if user_command not in special_commands:
                    wincc.execute_cmd(user_command)
                    if wincc.c.rowcount > 0:
                        for rec in wincc.c.fetchall():
                            print(unicode(rec))
                else:
                    exec(special_commands[user_command])
            except Exception as e:
                print(e)        
    except WinCCException as e:
        print('Connection to host failed. Quitting program. Bye.')    
    finally:    # disconnect
        wincc.close_connection()  

def interactive_mode_wincc(host, database):
    """Provides a shell for the user to interactively query the SQL server"""
    #special_user_commands = ['help', 'exit', 'databases', 'tables', 'database']
    help_text =  """Interactive mode with WinCCOLEDBProvider.1
exit:        Disconnect from server and quit program    
help:        Print this help text
tables:        Print table names of current databases
databases:    Print database names
database:        Print currently opened database
    """
    exit_message = "Disconnecting from server. Quitting interactive mode. Bye!"
    special_commands = {
                        'help': 'print(help_text)',
                        'exit': 'print(exit_message)\nloop=False',
                        'databases': 'wincc.fetch_database_names()\nwincc.print_database_names()',
                        'tables': 'wincc.print_table_names()',
                        'database': 'wincc.fetch_current_database_name()\nwincc.print_current_database_name()',
                        'alarms': 'wincc.fetch_alarms(user_input.split(" ")[1])\nwincc.print_alarms()',
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
                user_input_cmd = user_input.split(" ")[0]
                time_start = time.time()
                if user_input_cmd == 'tag':
                    print("Not implemented yet")
                elif user_input_cmd not in special_commands:                    
                    wincc.execute_cmd_wincc(user_input)
                    if wincc.c_wincc.rowcount > 0:
                        for rec in wincc.c_wincc.fetchall():
                            print(unicode(rec))                    
                else:
                    #print("exec: " + special_commands[user_input_cmd])
                    exec(special_commands[user_input_cmd])
                time_elapsed = time.time() - time_start
                print("Fetched data in {time}.".format(time=time_elapsed))
            except Exception as e:
                print(e)
                print(traceback.format_exc())        
    except WinCCException as e:
        print('Connection to host failed. Quitting program. Bye.')    
    finally:    # disconnect
        wincc.close_connection() 
            

@cli.command()
@click.argument('tagid')
@click.argument('begin_time')
@click.option('--end-time', '-e', default='', help='Can be absolute (see begin-time) or relative 0000-00-01[ 12:00:00[.000]]')
@click.option('--timestep', '-t', default=0, help='Group result in timestep long sections. Time in seconds.')
@click.option('--mode', '-m', default='first', help="Optional mode. Can be first, last, min, max, avg, sum, count, and every mode with an '_interpolated' appended e.g. first_interpolated.")
@click.option('--host', '-h', prompt=True, help='Hostname')
@click.option('--database', '-d', default='', help='Initial Database (Catalog).')
@click.option('--utc', default=False, is_flag=True, help='Activate utc time. Otherwise local time is used.')
def tag(tagid, begin_time, end_time, timestep, mode, host, database, utc):
    """Parse user friendly tag query and assemble userunfriendly wincc query""" 
    
    query = wincc_tag.query_builder(tagid, begin_time, end_time, timestep, mode, utc)
    print(query)
    
    time_start = time.time()
    
    # if database is not set, try to fetch it's name
    # Connect to host with SQLOLEDB Provider
    if database == '':
        try:
            print("Database not given. Trying to read it from server.")
            get_wincc_runtime_database(host)
        except Exception as e:
            print(e)
            print(traceback.format_exc()) 
        
    try:    
        # Conenct to WinCC Database
        wincc = wincc_mssql_connection(host, database)        
        wincc.connect_winccoledbprovider()
        
        # Execute query
        wincc.execute_cmd_wincc(query)
        
        # Print results   
        if wincc.c_wincc.rowcount > 0:
            print_tag_logging(wincc.c_wincc.fetchall())
            #for rec in wincc.c_wincc.fetchall():
            #    print rec
        
        time_elapsed = time.time() - time_start
        print("Fetched data in {time}.".format(time=time_elapsed))
        
    except Exception as e:
        print(e)
        print(traceback.format_exc())  
    
    wincc.close_connection()

def get_wincc_runtime_database(host):
    wincc = wincc_mssql_connection(host, '')
    wincc.connect()
    wincc.fetch_database_names()
    wincc.select_wincc_runtime_database()    
    database = wincc.wincc_runtime_database
    wincc.close_connection()
    return database

def get_wincc_config_database(host):
    wincc = wincc_mssql_connection(host, '')
    wincc.connect()
    wincc.fetch_database_names()
    wincc.select_wincc_config_database()    
    database = wincc.wincc_config_database
    wincc.close_connection()
    return database

@cli.command()
@click.argument('time')
def time_test(time):
    print datetime_to_str(local_time_to_utc(time))

@cli.command()
@click.argument('begin_time')
@click.option('--end-time', '-e', default='', help='Can be absolute (see begin-time) or relative 0000-00-01[ 12:00:00[.000]]')
@click.option('--text', default='', type= STRING_CP1252,help='Message text or part of message text.')
@click.option('--host', '-h', prompt=True, help='Hostname')
@click.option('--database', '-d', default='', help='Initial Database (Catalog).')
@click.option('--utc', default=False, is_flag=True, help='Activate utc time. Otherwise local time is used.')
@click.option('--show', '-s', default=False, is_flag=True, help="Don't actually query the db. Just show what you would do.")
@click.option('--state', default='',type=click.STRING, help="State condition e.g. '=2' or '>1'")
def alarms(begin_time, end_time, text, host, database, utc, show, state):
    # if database is not set, try to fetch it's name
    # Connect to host with SQLOLEDB Provider
    if database == '':
        try:
            print("Database not given. Trying to read it from server.")
            database = get_wincc_runtime_database(host)
        except Exception as e:
            print(e)
            print(traceback.format_exc()) 
            
    #wincc.fetch_alarms(user_input.split(" ")[1])\nwincc.print_alarms()
    query = wincc_alarm.query_builder(begin_time, end_time, text, utc, state)
        
    print(query)
    if not show:
        try:
            time_start = time.time()
            wincc = wincc_mssql_connection(host, database)
            wincc.connect_winccoledbprovider()
            wincc.execute_cmd_wincc(query)
            wincc.print_alarms()
            time_elapsed = time.time() - time_start
            print("Fetched data in {time}.".format(time=time_elapsed))    
        except Exception as e:
                print(e)
                print(traceback.format_exc()) 
        finally:
            wincc.close_connection()
            
            
@cli.command()
@click.argument('name')
@click.option('--host', '-h', prompt=True, help='Hostname')
@click.option('--database', '-d', default='', help='Initial Database (Catalog).')
def tagid_by_name(name, host, database):
    if database == '':
        try:
            print("Database not given. Trying to read it from server.")
            database = get_wincc_config_database(host)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
    try:
        wincc = wincc_mssql_connection(host, database)
        wincc.connect()
        wincc.execute_cmd("SELECT TLGTAGID, VARNAME FROM PDE#TAGs WHERE VARNAME LIKE '%{name}%'".format(name=name))
        if wincc.c.rowcount > 0:
            for rec in wincc.c.fetchall():
                print rec
        
    except Exception as e:
        print(e)
    finally:
        wincc.close_connection()
    

if __name__ == "__main__":
    cli()