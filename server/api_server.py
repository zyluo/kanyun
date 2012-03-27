# encoding: utf-8
# TAB char: space
# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-27
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-27

import sys
import time
import json
import db
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
"""

class STATISTIC:
    AVERAGE = 0
    MINIMUM = 1
    MAXIMUM = 2
    SUM     = 3
    SAMPLES = 4

"""cassandra database object"""
data_db = None
"""
# ColumnFamilys object collection
# data format: {key: ColumnFamily Object}
# example: {'cpu', ColumnFamily()}
"""
cfs = dict()

def api_init():
    global data_db
    config = ConfigParser.ConfigParser()
    config.read("demux.conf")
    server_cfg = dict(config.items('Demux'))
    data_db = pycassa.ConnectionPool('data', server_list=[server_cfg['db_host']])

def api_getdata(row_id, cf_str, scf_str, statistic, period=5, time_from=0, time_to=0):
    """
    statistic is STATISTIC enum
    period default=5 minutes
    time_to default=0(now)
    """
    global data_db
    global cfs
    
    if data_db is None:
        api_init()
    if not cfs.has_key(cf_str):
        print 'new connection:', cf_str
        cfs[cf_str] = pycassa.ColumnFamily(data_db, cf_str)
    cf = cfs[cf_str]
        
    if time_to == 0:
        time_to = time.time()
    
#    print "cf.get(%s, super_column=%s, column_start=%d, column_finish=%d)" % \
#        (row_id, scf_str, time_from, int(time_to))
    rs = cf.get(row_id, super_column=scf_str, column_start=time_from, column_finish=int(time_to))
    print rs
    
    return rs, len(rs)
    
class Statistics():
    def __init__(self):
        self.count = 0
        self.sum = 0
        self.min = 0
        self.max = 0
        self.previous = 0
    def update(self, value):
        self.count += 1
        self.sum += value
        if value > self.previous:
            self.max = value
        elif value < self.previous:
            self.min = value
        self.previous = value
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

def analyize_data(rs, period, statistic):
    """[private func]analyize the data and call callback func to statistic"""
    st = Statistics()
    this_min = dict()
    
    # get statistic data of each minute
    for t, value in rs.iteritems():
        #print t,"=",value
        rt = time.gmtime(t)
        key = rt.tm_min + rt.tm_hour*100 + rt.tm_mday*10000 + rt.tm_mon*1000000 + rt.tm_year*100000000
        st.update(int(value))
        this_min[key] = (st.get_agerage(), st.get_max(), st.get_min(), st.get_sum())
        
    print "each time:"
    for m, val in this_min.iteritems():
        print m, val
        
    # get the results
    t = 0
    st = Statistics()
    this_period = dict()
    for m, val in this_min.iteritems():
        if t == 0:
            t = m
        if m < t + period:
            st.update(int(val[0]))
            this_period[m] = (st.get_agerage(), st.get_max(), st.get_min(), st.get_sum())
        else:
            t = m
    print "each period:"
    for m, val in this_period.iteritems():
        print m, val
        
def api_statistic(row_id, cf_str, scf_str, statistic, period=5, time_from=0, time_to=0):
    rs, count = api_getdata(row_id, cf_str, scf_str, statistic, period, time_from, time_to)
    analyize_data(rs, period, statistic)
    
if __name__ == '__main__':

    config = ConfigParser.ConfigParser()
    config.read("demux.conf")
    server_cfg = dict(config.items('Demux'))

    context = zmq.Context()
    
    data_db = pycassa.ConnectionPool('data', server_list=[server_cfg['db_host']])
#    cf = pycassa.ColumnFamily(data_db, "cpu")
#    cf.get_range("instance-00000001@pyw.novalocal")

    # Socket to receive messages on
    handler = context.socket(zmq.REP)
    handler.bind("tcp://%(handler_host)s:%(handler_port)s" % server_cfg)
    print "listen tcp://%(handler_host)s:%(handler_port)s" % server_cfg

    # Socket to send messages on
    broadcast = context.socket(zmq.PUB)
    broadcast.bind("tcp://%(broadcast_host)s:%(broadcast_port)s" % server_cfg)
    print "listen tcp://%(broadcast_host)s:%(broadcast_port)s" % server_cfg

    # Socket with direct access to the feedback: used to syncronize start of batch
    feedback = context.socket(zmq.PULL)
    feedback.bind("tcp://%(feedback_host)s:%(feedback_port)s" % server_cfg)
    print "listen tcp://%(feedback_host)s:%(feedback_port)s" % server_cfg

    poller = zmq.Poller()
    poller.register(handler, zmq.POLLIN | zmq.POLLOUT)
    poller.register(feedback, zmq.POLLIN)

    # data DB
    data_db = pycassa.ConnectionPool('data', server_list=[server_cfg['db_host']])

    while True:
        socks = dict(poller.poll())
        
        # parse the command form client
        if socks.get(handler) == zmq.POLLIN:
            print 'REQ poolin'
            msg_type, msg_id, msg_json = handler.recv_multipart()
            msg_body = json.loads(msg_json)
            cli_msg = {'code': 200, 'desc': 'OK'}
            try:
                cmd = msg_body['cmd']
                msg = msg_body['msg']
                print cmd, msg
                print
                # access db and get return msg
                if cmd in ['read_lb', 'read_lb_list', 'read_load_balancer_id_all',
                           'read_http_server_name_all']:
                    db_res = getattr(db, cmd)(**msg)
                    cli_msg.update(db_res)
                elif cmd in ['create_lb', 'delete_lb', 'update_lb_config',
                             'update_lb_instances', 'update_lb_http_server_names']:
                    getattr(db, cmd)(**msg)
                    work_cmd = "update_lb" if cmd.startswith("update_lb") else cmd
                    work_msg = get_work_msg(cmd, **msg)
                    print ">>>>>>>>>", work_msg
                    print
                    broadcast.send_multipart([msg_type, msg_id,
                                              json.dumps({'cmd': work_cmd,
                                                          'msg': work_msg})])
                else:
                    raise Exception("Invalid command")
            except Exception, e:
                print traceback.format_exc()
                cli_msg['code'] = 500
                cli_msg['desc'] = str(e)
            print cmd, cli_msg
            print
            handler.send_multipart([msg_type, msg_id,
                                    json.dumps({'cmd': cmd,
                                                'msg': cli_msg})])

        # parse the data from worker and save to database
        if socks.get(feedback) == zmq.POLLIN:
            msg_type, report = feedback.recv_multipart()
            
            if plugins.has_key(msg_type) and len(report) > 0:
                report_str = ''.join(report)
                print 'recv(%s):%s' % (msg_type, report_str)
                data = json.loads(report_str)
                plugins[msg_type](data_db, data)
            else:
                print 'invaild data(%s):%s' % (msg_type, report_str)
            
