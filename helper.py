from datetime import datetime, timedelta, date
from dateutil import tz
from time import time
import logging


def str_to_date(dt_str):
    """Convert string of type "2015-08-27" to datetime object"""
    return datetime.strptime(dt_str, '%Y-%m-%d').date()


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
    if isinstance(dt_str, datetime):
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
    if isinstance(dt_in, str) or isinstance(dt_in, unicode):
        dt = str_to_datetime(dt_in)
    elif not isinstance(dt_in, datetime):
        raise TypeError("Wrong type. Expected: datetime or str. Got {type}."
                        .format(type=type(dt_in)))
    else:
        # datetime
        dt = dt_in

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
    t = time()
    return (lambda: (time() - t))


def eval_datetime(str_datetime):
    """Return datetime object for given string.

    Allow for keywords 'today', 'yesterday', 'yesterday-1', 'tomorrow'.

    Examples:
    >>> eval_datetime('2015-09-07')
    datetime.datetime(2015, 9, 7, 0, 0)

    eval_datetime('today')
    """
    if str_datetime == 'today':
        today = datetime.now().replace(hour=0, minute=0, second=0,
                                       microsecond=0)
        return today
    elif str_datetime == 'yesterday':
        today = datetime.now().replace(hour=0, minute=0, second=0,
                                       microsecond=0)
        return (today - timedelta(1))
    elif str_datetime == 'yesterday-1':
        today = datetime.now().replace(hour=0, minute=0, second=0,
                                       microsecond=0)
        return (today - timedelta(2))
    elif str_datetime == 'tomorrow':
        today = datetime.now().replace(hour=0, minute=0, second=0,
                                       microsecond=0)
        return (today + timedelta(1))
    else:
        return str_datetime


if __name__ == "__main__":
    import doctest
    doctest.testmod()
