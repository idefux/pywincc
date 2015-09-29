""""
This module holds extensions to wincc_connect that are specific to
company VAS Energy Systems.

This is parameter handling and calling of specific tag names.
"""
from __future__ import print_function
from joblib import Parallel, delayed
import multiprocessing
import logging
from wincc import do_tag_report
from datetime import timedelta
from helper import datetime_to_str

key_figures = {'ORC1_TURB_GEP': 729,
               'BMK1_BK_TEMP_IW': 878,
               'TOE1_KESS_VL_TEMP_IW': 726,
               'TOE1_WMZ1_POWER': 780,
               'TOE1_WMZ2_POWER': 781,
               'TOE1_POWER': 797,
               'BMK1_FUZZ_POWER': 10}


def get_daily_key_figures_avg(host_info, day):
    """Query DB for ORC power avg."""
    # tag_ids = []
    # for key in key_figures:
    #    tag_ids.append(key_figures[key])
    # wincc.
    logging.debug("Trying to retrieve daily key_figures for %s", day)
    begin_day = datetime_to_str(day)
    end_day = datetime_to_str(day + timedelta(1))
    tagids = [key_figures[key] for key in key_figures]
    num_cores = multiprocessing.cpu_count()
    logging.debug("Found %s cores", num_cores)
    Parallel(n_jobs=num_cores)(delayed(do_tag_report)
                              (host_info, begin_day, end_day, [tagid], 3600, 'avg')
                               for tagid in tagids)
    # Non-parallel version:
    # for tagid in tagids:
    #    do_tag_report(host_info, begin_day, end_day, [tagid], 3600, 'avg')
