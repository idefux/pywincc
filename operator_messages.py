#!/usr/bin/python
# -*- coding: utf-8 -*-

from helper import local_time_to_utc, str_to_datetime, datetime_to_str_without_ms

def om_query_builder(begin_time, end_time='', msg_text='', utc=False):
    """Build wincc operator message query string
    
    >>> om_query_builder("2015-08-25 02:12:00")
    u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE MsgNr = 12508141 AND DateTime > '2015-08-25 00:12:00'"
    
    >>> om_query_builder("2015-08-25 02:12:00", "2015-08-25 06:47:12")
    u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE MsgNr = 12508141 AND DateTime > '2015-08-25 00:12:00' AND DateTime < '2015-08-25 04:47:12'"
    
    >>> om_query_builder("2015-08-25 02:12:00", "2015-08-25 06:47:12", "Vorlauf")
    u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE MsgNr = 12508141 AND DateTime > '2015-08-25 00:12:00' AND DateTime < '2015-08-25 04:47:12' AND Text1 LIKE '%Vorlauf%'"
    """
    dt_begin_time = str_to_datetime(begin_time)
    if not utc:        
        dt_begin_time = local_time_to_utc(dt_begin_time)
    query = u"ALARMVIEW:SELECT * FROM ALGVIEWDEU WHERE MsgNr = 12508141 AND DateTime > '{begin}'".format(begin=datetime_to_str_without_ms(dt_begin_time))    

    if end_time != '':
        dt_end_time = str_to_datetime(end_time)
        if not utc:
            dt_end_time = local_time_to_utc(dt_end_time)
        query += u" AND DateTime < '{end}'".format(end=datetime_to_str_without_ms(dt_end_time))
        
    if msg_text != '':
        #print(type(msg_text))
        #query += u" AND Text1 LIKE '%{text}%'".format(text=msg_text.decode("iso-8859-1"))
        query += u" AND Text1 LIKE '%{text}%'".format(text=msg_text)
    
    return query
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()