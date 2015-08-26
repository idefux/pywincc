import click
import time
import traceback
import logging

from interactive import InteractiveModeWinCC, InteractiveMode

#from wincc_mssql_connection import wincc_mssql_connection, WinCCException
from wincc import wincc, WinCCException
from mssql import mssql, MsSQLException
from tag import tag_query_builder
from alarm import alarm_query_builder

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
@click.option('--debug', default=False, is_flag=True, help='Turn on debug mode. Will print some debug messages.')
def cli(debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
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
        #interactive_mode_wincc(host, database)
        shell = InteractiveModeWinCC(host, database)
        shell.run()
    else:
        shell = InteractiveMode(host, database)
        shell.run()

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
        m = mssql(host, database)
        m.connect()

        # fire SQL queries until user stops
        loop = True
        while loop:
            try:
                user_command = raw_input('Enter SQL command: ')
                if user_command not in special_commands:
                    m.execute(user_command)
                    if m.rowcount():
                        for rec in m.fetchall():
                            print(unicode(rec))
                else:
                    exec(special_commands[user_command])
            except Exception as e:
                print(e)        
    except MsSQLException as e:
        print('Connection to host failed. Quitting program. Bye.')    
    finally:    # disconnect
        m.close()              

@cli.command()
@click.argument('tagid', nargs=-1)
@click.argument('begin_time', nargs=1)
@click.option('--end-time', '-e', default='', help='Can be absolute (see begin-time) or relative 0000-00-01[ 12:00:00[.000]]')
@click.option('--timestep', '-t', default=0, help='Group result in timestep long sections. Time in seconds.')
@click.option('--mode', '-m', default='first', help="Optional mode. Can be first, last, min, max, avg, sum, count, and every mode with an '_interpolated' appended e.g. first_interpolated.")
@click.option('--host', '-h', prompt=True, help='Hostname')
@click.option('--database', '-d', default='', help='Initial Database (Catalog).')
@click.option('--utc', default=False, is_flag=True, help='Activate utc time. Otherwise local time is used.')
@click.option('--show', '-s', default=False, is_flag=True, help="Don't actually query the db. Just show what you would do.")
def tag(tagid, begin_time, end_time, timestep, mode, host, database, utc, show):
    """Parse user friendly tag query and assemble userunfriendly wincc query""" 
    
    query = tag_query_builder(tagid, begin_time, end_time, timestep, mode, utc)
    if show:
        print(query)
        return
    
    time_start = time.time()
            
    try:    
        w = wincc(host, database)        
        w.connect()
        w.execute(query)
        
        if w.rowcount():
            print_tag_logging(w.fetchall())
            #for rec in w.fetchall():
            #    print rec
        
        time_elapsed = time.time() - time_start
        print("Fetched data in {time}.".format(time=round(time_elapsed, 3)))
        
    except Exception as e:
        print(e)
        print(traceback.format_exc())  
    
    w.close()

#def get_wincc_runtime_database(host):
#    mssql = mssql(host, '')
#    mssql.connect()
#    mssql.fetch_database_names()
#    wincc.select_wincc_runtime_database()    
#    database = wincc.wincc_runtime_database
#    wincc.close_connection()
#    return database

#def get_wincc_config_database(host):
#    wincc = wincc_mssql_connection(host, '')
#    wincc.connect()
#    wincc.fetch_database_names()
#    wincc.select_wincc_config_database()    
#    database = wincc.wincc_config_database
#    wincc.close_connection()
#    return database

#@cli.command()
#@click.argument('time')
#def time_test(time):
#    print datetime_to_str(local_time_to_utc(time))

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
            
    query = alarm_query_builder(begin_time, end_time, text, utc, state)        
    print(query)
    
    if not show:
        try:
            time_start = time.time()
            w = wincc(host, database)
            w.connect()
            w.execute(query)
            w.print_alarms()
            time_elapsed = time.time() - time_start
            print("Fetched data in {time}.".format(time=round(time_elapsed,3)))    
        except WinCCException as e:
                print(e)
                print(traceback.format_exc()) 
        finally:
            w.close()
            
            
@cli.command()
@click.argument('name')
@click.option('--host', '-h', prompt=True, help='Hostname')
@click.option('--database', '-d', default='', help='Initial Database (Catalog).')
def tagid_by_name(name, host, database):
    if database == '':
        try:
            print("Database not given. Trying to read it from server.")
            w = wincc(host, database)
            database = w.fetch_wincc_config_database_name()
            w.close()
        except Exception as e:
            print(e)
            print(traceback.format_exc())
    try:
        w = wincc(host, database)
        w.connect()
        w.execute("SELECT TLGTAGID, VARNAME FROM PDE#TAGs WHERE VARNAME LIKE '%{name}%'".format(name=name))
        if w.rowcount():
            for rec in w.fetchall():
                print rec        
    except Exception as e:
        print(e)
    finally:
        w.close()
    

#@cli.command()
#@click.argument('begin_time')
#@click.argument('end_time')
#@click.option('--host', '-h', prompt=True, help='Hostname')
#@click.option('--database', '-d', default='', help='Initial Database (Catalog).')
#def report(begin_time, end_time, host, database):

#    print alarm_report(begin_time, end_time, )


if __name__ == "__main__":
    cli()