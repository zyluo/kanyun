#!/usr/bin/env python
# encoding: utf-8
# TAB char: space
#
#
# Author: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-4-6
# Last update: Peng Yuwei<pengyuwei@gmail.com> 2012-4-6
#

import logging


class MSG_TYPE:
    HEART_BEAT = '0'
    LOCAL_INFO = '1'
    TRAFFIC_ACCOUNTING = '2'
    AGENT = '3'
    
class STATISTIC:
    SUM     = 0
    MAXIMUM = 1
    MINIMUM = 2
    AVERAGE = 3
    SAMPLES = 4

statistic_str = dict()
statistic_str[STATISTIC.SUM] = "SUM"
statistic_str[STATISTIC.MAXIMUM] = "MAXIMUM"
statistic_str[STATISTIC.MINIMUM] = "MINIMUM"
statistic_str[STATISTIC.AVERAGE] = "AVERAGE"
statistic_str[STATISTIC.SAMPLES] = "SAMPLES"

