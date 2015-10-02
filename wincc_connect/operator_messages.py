#!/usr/bin/python
# -*- coding: utf-8 -*-

from .helper import local_time_to_utc, str_to_datetime, datetime_to_str_without_ms
from collections import namedtuple

OperatorMessage = namedtuple('OperatorMessage', 'datetime parameter parameter_translated old_value new_value username')


class OperatorMessageRecord():
    def __init__(self):
        self.operator_messages = []

    def push(self, operator_message):
        if isinstance(operator_message, OperatorMessage):
            self.operator_messages.append(operator_message)
        else:
            errormsg = "OperatorMessageRecord: Expected type 'OperatorMessage'. Got type {type}.".format(type=type(operator_message))
            raise TypeError(errormsg)

    def __get_parameter(self, operator_message):
        if operator_message.parameter_translated != u'':
            return operator_message.parameter_translated
        else:
            return operator_message.parameter

    def __unicode__(self):
        output = ""
        for om in self.operator_messages:
            output += u"{0}, '{1}', {2}, {3}, {4}\n".format(om.datetime, self.__get_parameter(om), om.old_value, om.new_value, om.username)
        return output

    def __str__(self):
        return unicode(self).encode('utf-8')

    def count(self):
        return len(self.operator_messages)

    def to_html(self):
        html = u"<table>\n"
        html += u"<tr>\n<th>Datetime</th><th>Parameter</th><th>Old Value</th><th>New Calue</th><th>Username</th>\n</tr>\n"
        for om in self.operator_messages:
            html += u"<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>\n".format(om.datetime, self.__get_parameter(om), om.old_value, om.new_value, om.username)
        html += u"</table>\n"
        return html  


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