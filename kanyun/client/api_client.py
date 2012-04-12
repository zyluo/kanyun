#!/usr/bin/env python

import sys
import time
import ConfigParser
import json
import zmq

from kanyun.common.const import *

# Author: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-27
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-4-5

"""
protocol:
[CMD, row_id, cf_str, scf_str, statistic, period, time_from, time_to]
example:
[u'S', u'instance-00000001@pyw.novalocal', u'cpu', u'total', 0, 5, 1332897600, 0]
"""

param_tmpl = ['S', u'instance-00000001@pyw.novalocal', u'cpu', u'total', 0, 5, 1332897600, 0]

def invoke(socket, param):
#    print "Sending request ", param
    socket.send (json.dumps(param))

    #  Get the reply.
    message = socket.recv()
#    print "Received reply ", "[", message, "]"
    
    return json.loads(message)
    
def invoke_getbykey2(socket, row_id, cf_str, scf_str):
    param = [u'G', row_id, cf_str, scf_str]
    r = invoke(socket, param)
    if r is None:
        r = dict()
#    for k, i in r.iteritems():
#        print "{%s:%s}" % (k, i)
#    print "%d results of cf=%s,scf=%s,key=%s" % (len(r), cf_str, scf_str, row_id)
    return r

def invoke_getInstacesList(socket, cf_str):
    param = [u'L', cf_str]
    r = invoke(socket, param)
    if r is None:
        r = list()
#    for i in r:
#        print "%s" % (i)
#    print "%d results of cf=%s" % (len(r), cf_str)
    return r
    
def invoke_getbykey(socket, row_id):
    ret = list()
    cmd = list()
    cmd.append([u'K', row_id, u"vmnetwork"])
    cmd.append([u'K', row_id, u"mem"])
    cmd.append([u'K', row_id, u"nic"])
    cmd.append([u'K', row_id, u"blk"])
    cmd.append([u'G', row_id, u"cpu", u"total"])
    
    for i in cmd:
        cf_str = i[2]
#        scf_str = i[3]
        r = invoke(socket, i)
        if r is None:
            r = dict()
#        print r
        ret.append(r)
#        for k, i in r.iteritems():
#            print "%s.%s %d results" % (cf_str, k, len(i))
#            timestr = time.strftime("%m-%d %H:%M:%S", time.localtime(float(k)))
#            print "%s %s=%s" % (timestr, cf_str, i)
#        print "%d results of cf=%s,scf=%s,key=%s" % (len(r), cf_str, scf_str, row_id)
    return ret
    
def invoke_statistics(api_client, row_id, cf_str, scf_str, statistic, period=5, time_from=0, time_to=0):
    #param_tmpl = ['S', 'instance-00000001@pyw.novalocal', 'cpu', 'total', 0, 5, 1332897600, 0]
    #  Do 10 requests, waiting each time for a response
    for request in range (1,2):
        # cmd, row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to
        param = ['S', row_id, cf_str, scf_str, int(statistic), int(period), int(time_from), int(time_to)]
        
        timestr1 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(time_from)))
        if int(time_to) == 0:
            timestr2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        else:
            timestr2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(time_to)))
        print 'statistics info of %s(period=%s)' % (row_id, period)
        #print 'time range:%s --> %s ' % (timestr1, timestr2)
        param[4] = 0
        param[5] = 2
        r = invoke(api_client, param)
        print 'SUM=', '(no result)' if r is None else r.values()[0]
        
        param[4] = 1
        r = invoke(api_client, param)
        print 'MAX=', '(no result)' if r is None else r.values()[0]
        
        param[4] = 2
        r = invoke(api_client, param)
        print 'MIN=', '(no result)' if r is None else r.values()[0]
        
        param[4] = 3
        r = invoke(api_client, param)
        print 'AVERAGE=', '(no result)' if r is None else r.values()[0]
    

class ApiClient():
    def __init__(self, api_host = '127.0.0.1', api_port = '5556'):
        # default value
        self.cf_str = u''
        self.scf_str = u''
        self.statistic = 0
        self.period = 5
        self.time_from = 0
        self.time_to = 0
        self.key = u''
        
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://%s:%s" % (api_host, api_port))
    def set_param(self, key=u'', cf_str=u'', scf_str=u'', statistic=0, period=5, time_from=0, time_to=0):
        self.cf_str = cf_str
        self.scf_str = scf_str
        self.statistic = statistic
        self.period = period
        self.time_from = time_from
        self.time_to = time_to
        self.key = key
    def invoke(self):
        param = ['S', self.key, self.cf_str, self.scf_str, int(self.statistic), int(self.period), int(self.time_from), int(self.time_to)]
        r = invoke(self.socket, param)
        return r
    def get_max(self):
        self.period = STATISTIC.SUM
        r = self.invoke()
        return None if r is None else r.values()[0]
    def get_min(self):
        self.period = STATISTIC.MINIMUM
        r = self.invoke()
        return None if r is None else r.values()[0]
    def get_sum(self):
        self.period = STATISTIC.SUM
        r = self.invoke()
        return None if r is None else r.values()[0]
    def get_average(self):
        self.period = STATISTIC.AVERAGE
        r = self.invoke()
        return None if r is None else r.values()[0]
    def get_result(self, s):
        self.statistic = s
        r = self.invoke()
        return r
    def getbykey(self, key, cf_str=None, scf_str=None):
        if cf_str is None or scf_str is None:
            return invoke_getbykey(self.socket, key)
        else:
            return invoke_getbykey2(self.socket, row_id, cf_str, scf_str)
    def getlist(self, cf_str):
        return invoke_getInstacesList(self.socket, cf_str)
