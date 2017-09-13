""" Helper Functions to handle WinCC Tag queries"""
from .helper import datetime_to_str, str_to_datetime, local_time_to_utc,\
    utc_to_local, utc_to_utcx, remove_timezone
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
            xs.append(remove_timezone(tag.time))
            ys.append(tag.value)
        return xs, ys

    def __unicode__(self):
        output = u"{0}: {1}\n".format(self.tagid, self.name)
        for tag in self:
            output += u"{time}: {value}\n".format(time=remove_timezone(tag.time),
                                                  value=tag.value)
        return output

    def __str__(self):
        return unicode(self).encode('utf-8')

    def to_csv(self, delimiter=',', name='', tz=''):
        output = ""
        if name != '':
            output = u"DateTime{}{}\n".format(delimiter, name)
        for tag in self:
            if not tz:
                output += u"{time}{delimiter}{value}\n".format(time=tag.time,
                                                               delimiter=delimiter,
                                                               value=tag.value)
            else:
                output += u"{time}{delimiter}{value}\n".format(time=utc_to_utcx(tag.time, tz),
                                                               delimiter=delimiter,
                                                               value=tag.value)
        return output

    def plot(self):
        from matplotlib import pyplot
        xs, ys = self.get_xs_ys()
        pyplot.plot(xs, ys)
        pyplot.xlim(min(xs), max(xs))
        pyplot.ylim(min(ys), max(ys))
        pyplot.show()


def plot_tag_records(tag_records, show=True, save=False):
    from matplotlib import pyplot
    from numpy import mean
    # from matplotlib.dates import date2num
    fig = pyplot.figure(1, figsize=(11.692, 8.267))
    num_rows = len(tag_records)
    num_cols = 1
    for i, records in enumerate(tag_records):
        pyplot.subplot(num_rows, num_cols, i+1)
        xs, ys = records.get_xs_ys()
        ys_mean = [mean(ys) for i in xs]
        # xs = date2num(xs)
        pyplot.plot(xs, ys, label=records.tagid, marker='o')
        pyplot.plot(xs, ys_mean, label='mean', linestyle='--')
        pyplot.legend()
    # fig = pyplot.gcf()
    if save:
        filename = ''
        for i, records in enumerate(tag_records):
            if i > 0:
                filename += '-'
            filename += str(records.tagid)
        filename_png = filename + '.png'
        filename_pdf = filename + '.pdf'
        fig.savefig(filename_png)
        fig.savefig(filename_pdf)
    if show:
        pyplot.show()


def plot_tag_records2(tag_records, plot_config=None, show=True, save=False):
    """Plot given tag_records."""
    from matplotlib import pyplot
    from numpy import mean
    num_figures = len(plot_config["figures"])
    figures = [None for _ in range(num_figures)]
    axes = [[] for _ in range(num_figures)]
    for figure_num in range(num_figures):
        fig, ax = pyplot.subplots(figsize=(11.692, 8.267))
        # figures.append(pyplot.figure(figsize=(11.692, 8.267)))
        figures[figure_num] = fig
        ax_ymin = plot_config["axes"][0]["min"]
        ax_ymax = plot_config["axes"][0]["max"]
        ax.set_ylim([ax_ymin, ax_ymax])
        axes[figure_num] = [ax]
        num_axes = plot_config["figures"][figure_num]["num_axes"]
        for axis_num in range(1, num_axes):
            new_ax = ax.twinx()
            ax_ymin = plot_config["axes"][axis_num]["min"]
            ax_ymax = plot_config["axes"][axis_num]["max"]
            new_ax.set_ylim([ax_ymin, ax_ymax])
            axes[figure_num].append(new_ax)
    # num_axes = len(plot_config["axes"])
    # fig, ax1 = pyplot.subplots(nrows=1, ncols=1,
    #                            figsize=(11.692, 8.267))

    # for figure_num, figure in enumerate(figures):
    #     num_axes = plot_config["figures"][figure_num]["num_axes"]
    #     figures[figure_num].add_subplot(1,1,1)
    #     for axis_num in range(num_axes):
    #         for i, record in enumerate(tag_records):
    #             tagid = record.tagid
    #             tagid_config = plot_config["tags"][tagid]
    #             if (tagid_config["figure_num"] == figure_num and
    #                 tagid_config[figure_num]["axis_num"] == axis_num):
    #                     if axis_num == 0:

    for i, records in enumerate(tag_records):
        xs, ys = records.get_xs_ys()
        ys_mean = [mean(ys) for _ in xs]
        tagid = str(records.tagid)
        figure_num = plot_config["tags"][tagid]["figure_num"]
        axis_num = plot_config["tags"][tagid]["axis_num"]
        tag_name = plot_config["tags"][tagid]["name"]
        ax = axes[figure_num][axis_num]
        ax.plot(xs, ys, label=tag_name, marker='o')
        ax.plot(xs, ys_mean, label='mean', linestyle='--')
        ax.legend()
    if save:
        filename = ''
        for i, records in enumerate(tag_records):
            if i > 0:
                filename += '-'
            filename += str(records.tagid)
        for figure_num, figure in enumerate(figures):
            filename_png = filename + "_" + str(figure_num) + '.png'
            filename_pdf = filename + "_" + str(figure_num) + '.pdf'
            figure.savefig(filename_png)
            figure.savefig(filename_pdf)
    if show:
        for figure in figures:
            figure.show()


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

    timestep_dict = {'m': 60, 'min': 60, 'minute': 60,
                     '1m': 60, '1min': 60, '1minute': 60,
                     '10m': 600, '10min': 600, '10minutes': 600,
                     '30m': 1800, '30min': 1800, '30minutes': 1800,
                     'half_hour': 1800, 'h': 3600, 'hour': 3600,
                     '1h': 3600, '1hour': 3600,
                     'd': 86400, 'day': 86400, '1d': 86400, '1day': 86400}

    if timestep:
        if timestep in timestep_dict:
            timestep = timestep_dict[timestep]
        else:
            timestep = int(timestep)

    if mode not in mode_dict:
        print("Error: {mode} is not a valid mode. Allowed modes are first, \
        last, min, max, avg, sum, count, and every mode with an '_interpolated'\
         appended e.g. first_interpolated").format(mode=mode)
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
        # relative time
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

    if timestep:
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
