from datetime import datetime, timedelta, date
from dateutil import tz
from time import time
import logging


def str_to_date(date_str):
    """Convert string to datetime object.
    Allowed string formats '2015-09-15', '2015-09'.
    '2015-09 will imply day 1.
    """
    if isinstance(date_str, date):
        return date_str
    try:
        date_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        date_date = datetime.strptime(date_str, '%Y-%m').date()
    return date_date


def date_to_str(dt):
    """Convert datetime object to e.g. "2015-08-27" """
    return dt.strftime('%Y-%m-%d')


def date_to_str_underscores(dt):
    """Convert to e.g. "2015_09_01" """
    return dt.strftime('%Y_%m_%d')


def datetime_to_str(dt):
    """Convert datetime object to e.g. "2015-08-21 10:22:10.483"""
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[0:-3]


def datetime_to_str_without_ms(dt):
    """Convert datetime to e.g. "2015-08-21 10:22:10"""
    return datetime_to_str(dt)[0:-4]


def datetime_to_str_underscores(dt):
    """Convert to e.g. "2015_01_21_10_22_10"""
    return dt.strftime('%Y_%m_%d_%H_%M_%S')


def datetime_to_str_slashes(dt):
    """Convert to e.g. "2015_01_21_10_22_10"""
    return dt.strftime('%d/%m/%Y %H:%M:%S')

def datetime_is_date(dt):
    """Return True if datetime object is a date (H, M, S == 0).

    In fact it does not return True, but a datetime.time object.
    datetime.time(0,0) is evaluated as False
    e.g. datetime.time(0,1) is evaluated as True
    So returning this object should be fine for my application
    """
    return not dt.time()


def str_to_datetime(dt_str):
    """Return a datetime object build from given string
    Allowed string types are "2015-08-21", "2015-08-21 10:23:25", \
    "2015-08-26 07:47" and "2015-08-21 10:23:48.672"

    Examples:

    >>> str_to_datetime("2015-08-21")
    datetime.datetime(2015, 8, 21, 0, 0)

    >>> str_to_datetime("2015-08-21 10:23:25")
    datetime.datetime(2015, 8, 21, 10, 23, 25)

    >>> str_to_datetime("2015-08-26 07:47")
    datetime.datetime(2015, 8, 26, 7, 47)

    >>> str_to_datetime("2015-08-21 10:23:48.672")
    datetime.datetime(2015, 8, 21, 10, 23, 48, 672000)

    """
    if isinstance(dt_str, datetime) or isinstance(dt_str, date):
        return dt_str
    try:
        t = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        try:
            t = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                t = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
            except ValueError:
                try:
                    t = datetime.strptime(dt_str, '%Y-%m-%d')
                except ValueError:
                    print("Could not parse datetime {dt}".format(dt=dt_str))
                    return None
    return t


def local_time_to_utc(dt_in):
    """Transform given datetime object from local timezone to UTC."""
    if isinstance(dt_in, datetime):
        dt = dt_in
    elif isinstance(dt_in, str) or isinstance(dt_in, unicode):
        dt = str_to_datetime(dt_in)
    else:
        raise TypeError("Wrong type. Expected: datetime or str. Got {type}."
                        .format(type=type(dt_in)))

    from_zone = tz.tzlocal()
    to_zone = tz.gettz('UTC')

    local_time = dt.replace(tzinfo=from_zone)
    return local_time.astimezone(to_zone)


def utc_to_local(t):
    """Transform given datetime object from UTC to local timezone."""
    from_zone = tz.gettz('UTC')
    to_zone = tz.tzlocal()
    # utc = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
    utc = t.replace(tzinfo=from_zone)
    return utc.astimezone(to_zone)


def utc_to_utcx(t, x):
    """Transform given datetime object from UTC to UTC+x"""
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('UTC+{}'.format(x))
    utc = t.replace(tzinfo=from_zone)
    return utc.astimezone(to_zone)


def daterange(start_date, end_date):
    """Iterable for days in given range. end_date is excluded."""
    for n in range(int((end_date - start_date).days)):
        logging.debug('Yielding date %s', start_date + timedelta(n))
        yield start_date + timedelta(n)


def tic():
    """Simple helper function for timing execution

    Returns a closure that holds current time when calling tic().

    Usage:
    toc = tic()
    //some code
    print(toc())
    """
    now = time()
    return lambda: (time() - now)


def today_as_datetime():
    """Return today's date as datetime.datetime object.
    Will look something like 'datetime.datetime(2015, 9, 9, 0, 0).
    """
    return datetime.now().replace(hour=0, minute=0,
                                  second=0, microsecond=0)


def yesterday_as_datetime():
    """Return yesterday's date as datetime.datetime object."""
    return today_as_datetime() - timedelta(1)


def eval_datetime(str_datetime):
    """Return datetime object for given string.

    Allow for keywords 'today', 'yesterday', 'yesterday-1', 'tomorrow'.

    Examples:
    >>> eval_datetime('2015-09-07')
    '2015-09-07'

    eval_datetime('today')
    """
    if str_datetime == 'today':
        today = today_as_datetime()
        return today
    elif str_datetime == 'yesterday':
        today = today_as_datetime()
        return (today - timedelta(1))
    elif str_datetime == 'yesterday-1':
        today = today_as_datetime()
        return (today - timedelta(2))
    elif str_datetime == 'tomorrow':
        today = today_as_datetime()
        return (today + timedelta(1))
    else:
        return str_datetime


def remove_timezone(dt_datetime):
    """Remove the timezone info from datetime object."""
    return dt_datetime.replace(tzinfo=None)


def get_next_month(dt_datetime):
    """Return a datetime or date object incremented by 1 month.

    Examples:
    >>> get_next_month(datetime(2015,9,15))
    datetime.datetime(2015, 10, 15, 0, 0)

    >>> get_next_month(datetime(2015,12,7).date())
    datetime.date(2016, 1, 7)
    """
    if dt_datetime.month < 12:
        next_month = dt_datetime.replace(month=dt_datetime.month+1)
    else:
        next_month = dt_datetime.replace(year=dt_datetime.year+1, month=1)
    return next_month


def datetime_to_syslog_timestamp(time):
    """Take a datetime object and return a string for syslog."""
    return time.strftime('%b %d %H:%M:%S')


if __name__ == "__main__":
    import doctest
    doctest.testmod()
