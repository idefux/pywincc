import click
import traceback
import logging

from wincc import wincc, WinCCException, do_alarm_report,\
    do_batch_alarm_report, do_operator_messages_report, WinCCHosts,\
    get_host_by_name, do_alarm_report_monthly
from alarm import alarm_query_builder
from tag import tag_query_builder, print_tag_logging, plot_tag_records
from interactive import InteractiveModeWinCC, InteractiveMode
from operator_messages import om_query_builder
from helper import tic, datetime_to_str_without_ms, eval_datetime,\
    str_to_datetime
from report import generate_alarms_report
from datetime import datetime, timedelta
from mssql import mssql
from vas import get_daily_key_figures_avg


class StringCP1252ParamType(click.ParamType):
    """String Param Type for click to curb with annoying windows cmd shell
    encoding problems. German Umlaute are not correctly read from cmd line
    if Parameter Type is click.String
    """
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


class HostInfo():

    def __init__(self):
        self.address = None
        self.database = None
        self.name = None
        self.description = None

    def add_hostinfo(self, host_address, database, hostname):
        if hostname:
            h = get_host_by_name(hostname)
            self.address = h.host_address
            self.database = h.database
            self.description = h.descriptive_name
            return
        elif host_address:
            self.address = host_address
            self.database = database
            return
        else:
            print('Either hostname or host must be specified. Quitting.')
            raise KeyError()


host_info = HostInfo()


@click.group()
@click.option('--debug', default=False, is_flag=True,
              help='Turn on debug mode. Will print some debug messages.')
@click.option('--host-address', '-h', default='',
              help='Host address e.g. 10.1.57.50')
@click.option('--database', '-d', default='',
              help='Initial Database (Catalog).')
@click.option('--hostname', '-n', default='',
              help="Hostname e.g. 'agro'. Hostname will be looked up in "
              "hosts.sav file.")
def cli(debug, host_address, database, hostname):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    host_info.add_hostinfo(host_address, database, hostname)


@cli.command()
@click.option('--wincc-provider', '-w', default=False, is_flag=True,
              help='Use WinCCOLEDBProvider.1 instead of SQLOLEDB.1')
def interactive(wincc_provider):
    if wincc_provider:
        # interactive_mode_wincc(host, database)
        shell = InteractiveModeWinCC(host_info.address, host_info.database)
        shell.run()
    else:
        shell = InteractiveMode(host_info.address, host_info.database)
        shell.run()


@cli.command()
@click.argument('tagid', nargs=-1)
@click.argument('begin_time', nargs=1)
@click.option('--end-time', '-e', default='', help='Can be absolute (see begin-time) or relative 0000-00-01[ 12:00:00[.000]]')
@click.option('--timestep', '-t', default=0, help='Group result in timestep long sections. Time in seconds.')
@click.option('--mode', '-m', default='first', help="Optional mode. Can be first, last, min, max, avg, sum, count, and every mode with an '_interpolated' appended e.g. first_interpolated.")
@click.option('--utc', default=False, is_flag=True, help='Activate utc time. Otherwise local time is used.')
@click.option('--show', '-s', default=False, is_flag=True, help="Don't actually query the db. Just show what you would do.")
def tag(tagid, begin_time, end_time, timestep, mode, utc, show):
    """Parse user friendly tag query and assemble userunfriendly wincc query"""
    query = tag_query_builder(tagid, begin_time, end_time, timestep, mode, utc)
    if show:
        print(query)
        return

    toc = tic()
    try:
        w = wincc(host_info.address, host_info.database)
        w.connect()
        w.execute(query)

        if w.rowcount():
            print_tag_logging(w.fetchall())
            # for rec in w.fetchall():
            #    print rec

        print("Fetched data in {time}.".format(time=round(toc(), 3)))

    except Exception as e:
        print(e)
        print(traceback.format_exc())
    finally:
        w.close()


@cli.command()
@click.argument('tagid', nargs=-1)
@click.argument('begin_time', nargs=1)
@click.option('--end-time', '-e', default='',
              help='Can be absolute (see begin-time) or relative \
              0000-00-01[ 12:00:00[.000]]')
@click.option('--timestep', '-t', default=0,
              help='Group result in timestep long sections. Time in seconds.')
@click.option('--mode', '-m', default='first',
              help="Optional mode. Can be first, last, min, max, avg, sum, \
              count, and every mode with an '_interpolated' appended e.g. \
              first_interpolated.")
@click.option('--utc', default=False, is_flag=True,
              help='Activate utc time. Otherwise local time is used.')
@click.option('--show', '-s', default=False, is_flag=True,
              help="Don't actually query the db. Just show what you would do.")
@click.option('--plot', '-p', default=False, is_flag=True,
              help="Open a window with the plotted data.")
def tag2(tagid, begin_time, end_time, timestep, mode, utc, show, plot):
    """Parse user friendly tag query input and assemble wincc tag query"""
    if timestep and not end_time:
        end_time = datetime_to_str_without_ms(datetime.now())

    query = tag_query_builder(tagid, begin_time, end_time, timestep, mode, utc)
    if show:
        print(query)
        return

    toc = tic()
    try:
        w = wincc(host_info.address, host_info.database)
        w.connect()
        w.execute(query)

        records = w.create_tag_records()
        print("Fetched data in {time}.".format(time=round(toc(), 3)))
        # print(tags)
        # tags.plot()
        for record in records:
            print(record)
        if plot:
            plot_tag_records(records)

    except Exception as e:
        print(e)
        print(traceback.format_exc())
    finally:
        w.close()


@cli.command()
@click.argument('begin_time')
@click.option('--end-time', '-e', default='',
              help='Can be absolute (see begin-time) or relative \
              0000-00-01[ 12:00:00[.000]]')
@click.option('--text', default='', type=STRING_CP1252,
              help='Message text or part of message text.')
@click.option('--utc', default=False, is_flag=True,
              help='Activate utc time. Otherwise local time is used.')
@click.option('--show', '-s', default=False, is_flag=True,
              help="Don't actually query the db. Just show what you would do.")
@click.option('--state', default='', type=click.STRING,
              help="State condition e.g. '=2' or '>1'")
@click.option('--report', '-r', default=False, is_flag=True,
              help="Print html alarm report")
@click.option('--report-hostname', '-rh', default='',
              help="Host description to be printed on report.")
def alarms(begin_time, end_time, text, utc, show, state,
           report, report_hostname):
    """Read alarms from given host in given time."""
    query = alarm_query_builder(eval_datetime(begin_time),
                                eval_datetime(end_time),
                                text, utc, state)

    if show:
        print(query)
        return

    try:
        toc = tic()
        w = wincc(host_info.address, host_info.database)
        w.connect()
        w.execute(query)

        if report:
            alarms = w.create_alarm_record()
            if report_hostname:
                host_description = report_hostname
            else:
                host_description = host_info.description
            if not end_time:
                end_time = datetime_to_str_without_ms(datetime.now())
            generate_alarms_report(alarms, begin_time, end_time,
                                   host_description, text)
            print(unicode(alarms))
        else:
            w.print_alarms()

        print("Fetched data in {time}.".format(time=round(toc(), 3)))
    except WinCCException as e:
        print(e)
        print(traceback.format_exc())
    finally:
        w.close()


@cli.command()
@click.argument('begin_time')
@click.option('--end-time', '-e', default='',
              help='Can be absolute (see begin-time) or relative \
              0000-00-01[ 12:00:00[.000]]')
@click.option('--text', default='', type=STRING_CP1252,
              help='Message text or part of message text.')
@click.option('--utc', default=False, is_flag=True,
              help='Activate utc time. Otherwise local time is used.')
@click.option('--show', '-s', default=False, is_flag=True,
              help="Don't actually query the db. Just show what you would do.")
def operator_messages(begin_time, end_time, text, utc, show):
    """Query db for operator messages."""
    query = om_query_builder(eval_datetime(begin_time),
                             eval_datetime(end_time), text, utc)
    if show:
        print(query)
        return

    try:
        toc = tic()
        w = wincc(host_info.address, host_info.database)
        w.connect()
        w.execute(query)
        w.print_operator_messages()
        print("Fetched data in {time}.".format(time=round(toc(), 3)))
    except WinCCException as e:
        print(e)
        print(traceback.format_exc())
    finally:
        w.close()


@cli.command()
@click.argument('tagname')
def tagid_by_name(tagname):
    """Search hosts db for tag entries matching the given name.
    Return tagid.
    """
    try:
        toc = tic()
        mssql_conn = mssql(host_info.address,
                           strip_R_from_db_name(host_info.database))
        mssql_conn.connect()
        mssql_conn.execute("SELECT TLGTAGID, VARNAME FROM PDE#TAGs WHERE "
                           "VARNAME LIKE '%{name}%'".format(name=tagname))
        if mssql_conn.rowcount():
            for rec in mssql_conn.fetchall():
                print rec
        print("Fetched data in {time}.".format(time=round(toc(), 3)))
    except Exception as e:
        print(e)
    finally:
        mssql_conn.close()


@cli.command()
@click.argument('begin_time')
@click.argument('end_time')
@click.option('--cache', is_flag=True, default=False,
              help='Cache alarms (pickle).')
@click.option('--use-cached', is_flag=True, default=False,
              help='Use cached alarms')
def alarm_report(begin_time, end_time, cache, use_cached):
    """Print report of alarms for given host in given time."""
    do_alarm_report(eval_datetime(begin_time), eval_datetime(end_time),
                    host_info.address, host_info.database,
                    cache, use_cached)


@cli.command()
@click.argument('begin_time')
@click.argument('end_time')
@click.option('--cache', is_flag=True, default=False,
              help='Cache alarms (pickle).')
@click.option('--use-cached', is_flag=True, default=False,
              help='Use cached alarms')
def operator_messages_report(begin_time, end_time, cache, use_cached):
    """Print report of operator messages for given host in given time."""
    do_operator_messages_report(eval_datetime(begin_time),
                                eval_datetime(end_time),
                                host_info.address, host_info.database,
                                cache, use_cached)


@cli.command()
@click.argument('begin_day')
@click.argument('end_day')
@click.option('--parallel', '-p', is_flag=True, default=False,
              help='Use multithreading for parallel queries.')
def batch_report(begin_day, end_day, parallel):
    """Print a report for each day starting from begin_day to end_day."""
    do_batch_alarm_report(eval_datetime(begin_day), eval_datetime(end_day),
                          host_info.address, host_info.database,
                          host_info.description, parallel=parallel)


@cli.command()
@click.argument('begin_day')
def alarm_report_monthly(begin_day):
    do_alarm_report_monthly(begin_day, host_info.address, host_info.database,
                            host_info.description)


@cli.command()
@click.argument('begin_day')
@click.argument('end_day')
@click.option('--timestep', '-t', help='Time interval [day|week|month].')
def alarm_report2(begin_day, end_day, timestep):
    """Generate report(s) for known host."""
    do_batch_alarm_report(eval_datetime(begin_day), eval_datetime(end_day),
                          host_info.address, host_info.database,
                          host_info.description, timestep)


@cli.command()
def parameters():
    """Connect to host and retrieve parameter list."""
    mssql_conn = mssql(host_info.address,
                       strip_R_from_db_name(host_info.database))
    mssql_conn.connect()
    params = mssql_conn.create_parameter_record()
    mssql_conn.close()
    print(params)


@cli.command()
@click.argument('day')
def daily_perf_report(day):
    report_day = str_to_datetime(day)
    get_daily_key_figures_avg(host_info, report_day)


def strip_R_from_db_name(database):
    """Strip the 'R' from db name if present. Else do nothing.
    Examples:
    >>> strip_R_from_db_name('CC_OS_1__15_08_01_12_45_57R')
    'CC_OS_1__15_08_01_12_45_57'
    >>> strip_R_from_db_name('CC_OS_1__15_08_01_12_45_59')
    'CC_OS_1__15_08_01_12_45_59'
    """
    if database.endswith('R'):
        return database[:-1]
    return database


if __name__ == "__main__":
    #import doctest
    #doctest.testmod()
    cli()
