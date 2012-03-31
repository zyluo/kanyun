# encoding: utf-8
# TAB char: space
# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-27
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-28

import sys
import time
import json
import traceback
import ConfigParser
import zmq
import pycassa


"""
Save the vm's system info data to db.
                         +--- <-- Worker's PUSH
                         |
                         |
                   +----------+
                   |   PULL   |     <-- feedback
               +---|==========|
   Client--->  |REP|  Server  |
               +---|==========|
                   |   PUB    |     <-- broadcast
                   +----------+
                         |
                         |
                         +----> Worker's SUB
                         +----> DB

protocol:
    http://wiki.sinaapp.com/doku.php?id=monitoring
[u'S', u'instance-00000001@pyw.novalocal', u'cpu', u'total', 0, 5, 1332897600, 0]
"""

class STATISTIC:
    SUM     = 0
    MAXIMUM = 1
    MINIMUM = 2
    AVERAGE = 3
    SAMPLES = 4

class Statistics():
    def __init__(self):
        self.first = True
        self.count = 0
        self.sum = 0.0
        self.min = 0.0
        self.max = 0.0
        self.previous = 0.0
        self.diff = 0.0
    def update(self, value):
        self.count += 1
        self.sum += value
        if self.first:
            self.first = False
            self.previous = value
            self.max = value
            self.min = value
            return
            
        if value > self.previous:
            self.max = value
        elif value < self.previous:
            self.min = value
        self.diff = value - self.previous
        self.previous = value
    def get_value(self, which):
        if which == STATISTIC.AVERAGE:
            return self.get_agerage()
        elif which == STATISTIC.MINIMUM:
            return self.get_min()
        elif which == STATISTIC.MAXIMUM:
            return self.get_max()
        elif which == STATISTIC.SUM:
            return self.get_sum()
        elif which == STATISTIC.SAMPLES:
            return self.get_samples()
        else:
            # error
            print 'error:', which
            return 0
            
    def get_diff(self):
        return self.diff;
    def get_agerage(self):
        if self.count == 0:
            return 0
        else:
            return self.sum / self.count
    def get_sum(self):
        return self.sum
    def get_max(self):
        return self.max
    def get_min(self):
        return self.min
    def get_samples(self):
        # TODO
        return 0;


"""cassandra database object"""
data_db = None
"""
# ColumnFamilys object collection
# data format: {key: ColumnFamily Object}
# example: {'cpu', ColumnFamily()}
"""
cfs = dict()

def init_api():
    global data_db
    config = ConfigParser.ConfigParser()
    config.read("demux.conf")
    server_cfg = dict(config.items('Demux'))
    data_db = pycassa.ConnectionPool('data', server_list=[server_cfg['db_host']])

def get_cf2(cf_str):
    """[private]"""
    global data_db
    global cfs
    
    if data_db is None:
        init_api()
    if not cfs.has_key(cf_str):
        print 'new connection:', cf_str
        cfs[cf_str] = pycassa.ColumnFamily()
    cf = cfs[cf_str]
    return cf
    
def get_cf(cf_str):
    """[private]"""
    global data_db
    global cfs
    
    if data_db is None:
        init_api()
    if not cfs.has_key(cf_str):
        print 'new connection:', cf_str
        cfs[cf_str] = pycassa.ColumnFamily(data_db, cf_str)
    cf = cfs[cf_str]
    return cf
     
    
def api_getdata(row_id, cf_str, scf_str, time_from=0, time_to=0):
    """
    return: recordset, count, bool(count > limit?)
    """
    cf = get_cf(cf_str)
        
    if time_to == 0:
        time_to = time.time()
    
#    print "cf.get(%s, super_column=%s, column_start=%d, column_finish=%d)" % \
#        (row_id, scf_str, time_from, float(time_to))
    try:
        rs = cf.get(row_id, super_column=scf_str, column_start=time_from, column_finish=int(float(time_to)), column_count=20000)
        count = len(rs)
    except pycassa.cassandra.c10.ttypes.NotFoundException:
        rs = None
        count = 0
    #print rs
    
    return rs, count, False if (count == 20000) else True
    
def analyize_data(rs, period, statistic):
    """[private func]analyize the data"""
    if rs is None:
        return
    t = 0
    key_time = 0
    st = Statistics()
    this_period = dict()
    
    for timestmp, value in rs.iteritems():
        rt = time.gmtime(timestmp)
        key = rt.tm_min + rt.tm_hour*100 + rt.tm_mday*10000 + rt.tm_mon*1000000 + rt.tm_year*100000000
        if t == 0:
            print '\tget first value'
            t = key
            key_time = time.gmtime(timestmp)
        if key >= t + period:
            print '\tnext'
            t = key
            key_time = time.gmtime(timestmp)
        st.update(float(value))
        key2 = time.mktime((key_time.tm_year, key_time.tm_mon, key_time.tm_mday, key_time.tm_hour, key_time.tm_min,0,0,0,0))
        this_period[key2] = st.get_value(statistic)
        print '\tcompute time=:%d, value=%s(%f) "update(%s)=%d"' % \
                (key, value, float(value), key2, this_period[key2])
            
    print statistic, ":each period(", period, "):"
    for m, val in this_period.iteritems():
        print '\t', m, val
        
    return this_period

############################# public API interface #############################

def api_getbykey(row_id, cf_str, scf_str):
    """
    return: recordset, count, bool(count > limit?)
    """
    cf = get_cf(cf_str)
        
    if time_to == 0:
        time_to = time.time()
    
#    print "cf.get(%s, super_column=%s, column_start=%d, column_finish=%d)" % \
#        (row_id, scf_str, time_from, float(time_to))
    try:
        rs = cf.get(row_id, super_column=scf_str, column_start=time_from, column_finish=int(float(time_to)), column_count=20000)
        count = len(rs)
    except pycassa.cassandra.c10.ttypes.NotFoundException:
        rs = None
        count = 0
    #print rs
    
    return rs, count, False if (count == 20000) else True
    
    
def api_statistic(row_id, cf_str, scf_str, statistic, period=5, time_from=0, time_to=0):
    """statistic is STATISTIC enum
    period default=5 minutes
    time_to default=0(now)"""
    ret_len = 0
    rs, count, all_data = api_getdata(row_id, cf_str, scf_str, time_from, time_to)
    if not rs is None and count > 0:
        buf = analyize_data(rs, 1, statistic)
        ret = analyize_data(buf, period, statistic)
        ret_len = len(ret)
        print ret_len, "result."
    else:
        print "no result."
        ret = None
        ret_len = 0
    return ret, ret_len, all_data

########################## end public API interface #############################

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read("demux.conf")
    server_cfg = dict(config.items('Demux'))

    context = zmq.Context()
    
    data_db = pycassa.ConnectionPool('data', server_list=[server_cfg['db_host']])

    # Socket to receive messages on
    api_server = context.socket(zmq.REP)
    api_server.bind("tcp://%(api_host)s:%(api_port)s" % server_cfg)
    print "listen tcp://%(api_host)s:%(api_port)s" % server_cfg

    # data DB
    data_db = pycassa.ConnectionPool('data', server_list=[server_cfg['db_host']])

    while True:
        message = api_server.recv()
        msg = json.loads(message)
        
        if msg[0] == 'S':
            #[u'S', u'instance-00000001@pyw.novalocal', u'cpu', u'total', 0, 5, 1332897600, 0]
            print '*' * 60
            print "recv:", msg
            row_id = msg[1]
            cf_str = msg[2]
            scf_str = msg[3]
            statistic = msg[4]
            period = msg[5]
            time_from = msg[6]
            time_to = msg[7]
            rs, count, _ = api_statistic(row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to)
            api_server.send (json.dumps(rs))
        elif msg[0] == 'G':
            print '*' * 60
            print "recv:", msg
            row_id = msg[1]
            cf_str = msg[2]
            scf_str = msg[3]
            rs, count, _ = api_getbykey(row_id, cf_str, scf_str)
            api_server.send (json.dumps(rs))
        else:
            api_server.send (json.dumps([]))
            continue

