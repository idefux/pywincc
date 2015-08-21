""" Helper Functions to handle WinCC Tag queries"""

def query_builder(tagid, begin_time, end_time, timestep, mode):
    """Build the WinCC query string for reading tags"""
    
    mode_dict = {'first': 1, 'last': 2, 'min': 3, 'max': 4, 'avg': 5, 'sum': 6, 'count':7,
                     'first_interpolated': 257, 'last_interpolated': 258, 'min_interpolated': 259, 'max_interpolated': 260, 
                     'avg_interpolated': 261, 'sum_interpolated': 262, 'count_interpolated': 263}
        
    if mode not in mode_dict:
        print("Error: {mode} is not a valid mode. Allowed modes are first, last, min, max, avg, sum, count, and every mode with an '_interpolated' appended e.g. first_interpolated").format(mode=mode)
        return False
    
    mode_num = mode_dict[mode]
    
    query = "TAG:R,{tagid},'{begin_time}'".format(tagid=tagid, begin_time=begin_time)
    
    if end_time != '':
        query += ",'{end_time}'".format(end_time=end_time)
    
    if timestep != 0:
        query += ",'TIMESTEP={timestep},{mode}'".format(timestep=timestep, mode=mode_num)
        
    return query