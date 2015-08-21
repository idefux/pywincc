from datetime import datetime
from dateutil import tz

def datetime_to_str(dt):
    """Convert to e.g. "2015-08-21 10:22:10.483"""
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[0:-3]

def datetime_to_str_without_ms(dt):
    """Convert datetime to e.g. "2015-08-21 10:22:10"""
    return datetime_to_str(dt)[0:-4]

def str_to_datetime(dt_str):
    """Convert strings of type "2015-08-21", "2015-08-21 10:23:25" and "2015-08-21 10:23:48.672" to datetime object"""
    print("Trying to convert {dt} to UTC".format(dt=dt_str))
    try:
        t = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        try:
            t = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                t = datetime.strptime(dt_str, '%Y-%m-%d')
            except:
                print("Could not parse datetime {dt}".format(dt=dt_str))
                return None
    return t 

def local_time_to_utc(dt_in):
    """Expects a datetime or str object in local time and transforms it to UTC"""
    if isinstance(dt_in, str) or isinstance(dt_in, unicode):
        dt = str_to_datetime(dt_in)
    elif not isinstance(dt_in, datetime):
        raise TypeError("Wrong type for 'local_time_to_utc'. Expected: datetime or str. Got {type}.".format(type=type(dt_in)))
    else:
        #datetime
        dt = dt_in
    
    from_zone = tz.tzlocal()
    to_zone = tz.gettz('UTC')
               
    local_time = dt.replace(tzinfo=from_zone)
    return local_time.astimezone(to_zone)

def utc_to_local_time(t):    
    """ Expects a datetime object in utc timezone and transforms it to local timezone"""
    from_zone = tz.gettz('UTC')
    to_zone = tz.tzlocal()        
    #utc = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')        
    utc = t.replace(tzinfo=from_zone)        
    return utc.astimezone(to_zone)