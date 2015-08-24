""" Helper Functions to handle WinCC Tag queries"""
from helper import datetime_to_str, str_to_datetime, local_time_to_utc

def query_builder(tagid, begin_time, end_time, timestep, mode, utc):
    """Build the WinCC query string for reading tags
    
    >>> query_builder(132, "2015-08-24 10:48:10", "2015-08-24 10:49:24", 3600, 'sum', False)
    "TAG:R,132,'2015-08-24 08:48:10.000','2015-08-24 08:49:24.000','TIMESTEP=3600,6'"
    
    """
    
    mode_dict = {'first': 1, 'last': 2, 'min': 3, 'max': 4, 'avg': 5, 'sum': 6, 'count':7,
                     'first_interpolated': 257, 'last_interpolated': 258, 'min_interpolated': 259, 'max_interpolated': 260, 
                     'avg_interpolated': 261, 'sum_interpolated': 262, 'count_interpolated': 263}
        
    if mode not in mode_dict:
        print("Error: {mode} is not a valid mode. Allowed modes are first, last, min, max, avg, sum, count, and every mode with an '_interpolated' appended e.g. first_interpolated").format(mode=mode)
        return False
    
    mode_num = mode_dict[mode]
    
    if begin_time[0:4] == '0000': 
        #relative time
        query = "TAG:R,{tagid},'{begin_time}'".format(tagid=tagid, begin_time=begin_time)
    else:
        dt_begin_time = str_to_datetime(begin_time)
        if not utc:        
            dt_begin_time = local_time_to_utc(dt_begin_time)
        query = "TAG:R,{tagid},'{begin_time}'".format(tagid=tagid, begin_time=datetime_to_str(dt_begin_time))
    
    if end_time != '':
        if end_time[0:4] == '0000':            
            query += ",'{end_time}'".format(end_time=end_time)
        else:
            dt_end_time = str_to_datetime(end_time)
            if not utc:
                dt_end_time = local_time_to_utc(dt_end_time)
            query += ",'{end_time}'".format(end_time=datetime_to_str(dt_end_time))
    
    if timestep != 0:
        query += ",'TIMESTEP={timestep},{mode}'".format(timestep=timestep, mode=mode_num)
        
    return query

if __name__ == "__main__":
    import doctest
    doctest.testmod()