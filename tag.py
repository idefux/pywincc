""" Helper Functions to handle WinCC Tag queries"""
from helper import datetime_to_str, str_to_datetime, local_time_to_utc,\
    utc_to_local
from collections import namedtuple

Tag = namedtuple('Tag', 'time value')


class TagRecord():
    """Allows for storage and manipulation of a tags record"""

    def __init__(self, tagid='', name=''):
        """Initialize empty record."""
        self.tags = []
        self.tagid = tagid
        self.name = name

    def __iter__(self):
        return iter(self.tags)

    def push(self, tag):
        self.tags.append(tag)

    def get_xs_ys(self):
        xs = []
        ys = []
        for tag in self:
            xs.append(tag.time)
            ys.append(tag.value)
        return xs, ys

    def __unicode__(self):
        output = ""
        for tag in self:
            output += u"{time}: {value}\n".format(time=tag.time,
                                                  value=tag.value)
        return output

    def __str__(self):
        return unicode(self).encode('utf-8')

    def to_csv(self):
        output = ""
        for tag in self:
            output += u"{time};{value}\n".format(time=tag.time,
                                                 value=tag.value)
        return output

    def plot(self):
        from matplotlib import pyplot
        xs, ys = self.get_xs_ys()
        pyplot.plot(xs, ys)
        pyplot.xlim(min(xs), max(xs))
        pyplot.ylim(min(ys), max(ys))
        pyplot.show()


def tag_query_builder(tagids, begin_time, end_time, timestep, mode, utc):
    """Build the WinCC query string for reading tags

    >>> tag_query_builder(132, "2015-08-24 10:48:10", "2015-08-24 10:49:24", 3600, 'sum', False)
    "TAG:R,132,'2015-08-24 08:48:10.000','2015-08-24 08:49:24.000','TIMESTEP=3600,6'"
    """

    mode_dict = {'first': 1, 'last': 2, 'min': 3, 'max': 4, 'avg': 5, 'sum': 6,
                 'count': 7, 'first_interpolated': 257,
                 'last_interpolated': 258, 'min_interpolated': 259,
                 'max_interpolated': 260, 'avg_interpolated': 261,
                 'sum_interpolated': 262,
                 'count_interpolated': 263}

    if mode not in mode_dict:
        print("Error: {mode} is not a valid mode. Allowed modes are first, last, min, max, avg, sum, count, and every mode with an '_interpolated' appended e.g. first_interpolated").format(mode=mode)
        return False

    mode_num = mode_dict[mode]

    if len(tagids) == 1:
        query = "TAG:R,{tagid}".format(tagid=tagids[0])
    else:
        query = "TAG:R,("
        for tagid in tagids:
            query += "{tagid};".format(tagid=tagid)
        query = query[0:-1] + ")"

    if begin_time[0:4] == '0000':
        #relative time
        query += ",'{begin_time}'".format(begin_time=begin_time)
    else:
        dt_begin_time = str_to_datetime(begin_time)
        if not utc:
            dt_begin_time = local_time_to_utc(dt_begin_time)
        query += ",'{begin_time}'".format(begin_time=datetime_to_str(dt_begin_time))

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


def print_tag_logging(records):
    """Pretty print of tag logging recordset

    >>> print_tag_logging([(u'1776', u'2015-08-23 12:47:54', u'29.654', u'147', u'8425473')])
    '2015-08-23 14:47:54.000': 29.654.
    """
    for rec in records:
        print("{tagid}, {datetime}: {value}.".format(tagid=rec[0], datetime=datetime_to_str(utc_to_local(str_to_datetime(rec[1]))), value=rec[2]))
        # print rec


if __name__ == "__main__":
    import doctest
    doctest.testmod()