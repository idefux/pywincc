#!/usr/bin/python
# -*- coding: utf-8 -*-

from helper import local_time_to_utc, datetime_to_str_without_ms,\
    str_to_datetime

def query_builder(begin_time, end_time, msg_text, utc, state):
    """Build wincc alarm query string
    
    >>> query_builder("2015-08-24 10:07:48", "2015-08-24 10:08:12", '', False, '')
    u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE DateTime > '2015-08-24 08:07:48' AND DateTime < '2015-08-24 08:08:12'"
    
    >>> query_builder("2015-08-24 10:07:48", "2015-08-24 10:08:12", '', True, '')
    u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE DateTime > '2015-08-24 10:07:48' AND DateTime < '2015-08-24 10:08:12'"
    
    >>> query_builder("2015-08-24 10:07:48", '', '', False, '')
    u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE DateTime > '2015-08-24 08:07:48'"
    
    >>> query_builder("2015-08-24 10:07:48", '', 'Trogkettenf', False, '')
    u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE DateTime > '2015-08-24 08:07:48' AND Text1 LIKE '%Trogkettenf%'"
    
    >>> query_builder("2015-08-24 10:07:48", '', '', False, '>2')
    u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE DateTime > '2015-08-24 08:07:48' AND State >2"
    
    No relative time statements at alarms
    
    """    
    
    dt_begin_time = str_to_datetime(begin_time)
    if not utc:        
        dt_begin_time = local_time_to_utc(dt_begin_time)
    query = u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE DateTime > '{begin}'".format(begin=datetime_to_str_without_ms(dt_begin_time))  
    

    if end_time != '':
        dt_end_time = str_to_datetime(end_time)
        if not utc:
            dt_end_time = local_time_to_utc(dt_end_time)
        query += u" AND DateTime < '{end}'".format(end=datetime_to_str_without_ms(dt_end_time))
    
    #if msg_id != '':
    #    query += " AND MsgNr = {id}".format(id=msg_id)
    
    if msg_text != '':
        #print(type(msg_text))
        #query += u" AND Text1 LIKE '%{text}%'".format(text=msg_text.decode("iso-8859-1"))
        query += u" AND Text1 LIKE '%{text}%'".format(text=msg_text)
    
    if state != '':
        query += u" AND State {state_condition}".format(state_condition=state)
    
    return query

if __name__ == "__main__":
    import doctest
    doctest.testmod()