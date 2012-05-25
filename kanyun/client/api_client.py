# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 Sina Corporation
# All Rights Reserved.
# Author: YuWei Peng <pengyuwei@gmail.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys
import time
import ConfigParser
import json
import zmq
import uuid

from kanyun.common.const import *


"""
protocol:
[CMD, row_id, cf_str, scf_str, statistic, period, time_from, time_to]
example:
[u'S', u'instance-00000001@pyw.novalocal', u'cpu', u'total', 0, 5, 1332897600, 0]
"""

PROTOCOL_REQUEST = {
    'method': '',
    'args':  {
            
        }
    }
    
param_tmpl = {
    'method': 'query_usage_report',
    'args': {
        'id': "",
        'metric': "",
        'metric_param': 'vnet0',
        'statistic': 'sum',
        'period': 0,
        'timestamp_from': '2012-02-20T12:12:12',
        'timestamp_to': '2012-02-22T12:12:12',
    }
}

#def invoke(socket, param):
##    socket.send (json.dumps(param))

##    #  Get the reply.
##    message = socket.recv()
##    
##    return json.loads(message)
#    socket.send_multipart(['kanyun', '0', json.dumps(param)])

#    msg_type, uuid, message = socket.recv_multipart()
#    return json.loads(message)
#    
#def invoke_getbykey2(socket, row_id, cf_str, scf_str):
#    param = [u'G', row_id, cf_str, scf_str]
#    r = invoke(socket, param)
#    if r is None:
#        r = dict()
#    return r


#def invoke_getInstacesList(socket, cf_str):
#    param = [u'L', cf_str]
#    r = invoke(socket, param)
#    if r is None:
#        r = list()
#    return r
#    
#def invoke_getbykey(socket, row_id):
#    ret = list()
#    cmd = list()
#    cmd.append([u'K', row_id, u"vmnetwork"])
#    cmd.append([u'K', row_id, u"mem"])
#    cmd.append([u'K', row_id, u"nic"])
#    cmd.append([u'K', row_id, u"blk"])
#    cmd.append([u'G', row_id, u"cpu", u"total"])
#    
#    for i in cmd:
#        cf_str = i[2]
#        r = invoke(socket, i)
#        if r is None:
#            r = dict()
#        ret.append(r)
#    return ret
#    
#    
#def invoke_statistics(api_client, row_id, cf_str, scf_str, 
#                      statistic, period=5, time_from=0, time_to=0):
#    #param_tmpl = ['S', 'instance-00000001@pyw.novalocal', 'cpu', 'total', 0, 5, 1332897600, 0]
#    #  Do 10 requests, waiting each time for a response
#    for request in range (1,2):
#        # cmd, row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to
#        param = ['S', row_id, cf_str, scf_str, int(statistic), int(period), int(time_from), int(time_to)]
#        
#        timestr1 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(time_from)))
#        if int(time_to) == 0:
#            timestr2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#        else:
#            timestr2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(time_to)))
#        print 'statistics info of %s(period=%s)' % (row_id, period)
#        #print 'time range:%s --> %s ' % (timestr1, timestr2)
#        param[4] = 0
#        param[5] = 2
#        r = invoke(api_client, param)
#        print 'SUM=', '(no result)' if r is None else r.values()[0]
#        
#        param[4] = 1
#        r = invoke(api_client, param)
#        print 'MAX=', '(no result)' if r is None else r.values()[0]
#        
#        param[4] = 2
#        r = invoke(api_client, param)
#        print 'MIN=', '(no result)' if r is None else r.values()[0]
#        
#        param[4] = 3
#        r = invoke(api_client, param)
#        print 'AVERAGE=', '(no result)' if r is None else r.values()[0]
#    

class ApiClient():

    def __init__(self, api_host='127.0.0.1', api_port='5556'):
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
        
    ###################### Public API interface #########################
    def query_usage_report(self, msg):
        msg_type = 'kanyun'
        msg_uuid = str(uuid.uuid4())
        self.socket.send_multipart([msg_type, msg_uuid,
                                     json.dumps(msg)])
        r_msg_type, r_msg_uuid, r_msg_body = self.socket.recv_multipart()
        result = json.loads(r_msg_body)
        return result
    def list_instaces(self, metric):
        data = PROTOCOL_REQUEST
        data['method'] = "list_instance"
        data['args']['metric'] = metric
        resp = self.send(data)
        return resp
    ################## End public API interface ########################
    def send(self, data):
        msg_type = 'kanyun'
        msg_uuid = str(uuid.uuid4())
        self.socket.send_multipart([msg_type, msg_uuid,
                                     json.dumps(data)])
        r_msg_type, r_msg_uuid, r_msg_body = self.socket.recv_multipart()
        result = json.loads(r_msg_body)
        return result
        
    def set_param(self, key=u'', cf_str=u'', scf_str=u'', 
                  statistic='avg', period=5, time_from=None, time_to=None):
        self.cf_str = cf_str
        self.scf_str = scf_str
        self.statistic = statistic
        self.period = period
        if time_from is None:
            self.time_from = time.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            self.time_from = time_from
        if time_to is None:
            self.time_to = time.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            self.time_to = time_to
        self.key = key
        
    def invoke(self):
        param = {
            'method': 'query_usage_report',
            'args': {
                'id': self.key,
                'metric': self.cf_str,
                'metric_param': self.scf_str,
                'statistic': self.statistic,
                'period': int(self.period),
                'timestamp_from': self.time_from,
                'timestamp_to': self.time_to,
            }
        }
        
        socket.send_multipart(['kanyun', '0', json.dumps(param)])
        msg_type, uuid, message = socket.recv_multipart()
        
        return json.loads(message)
        
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
        
#    def getbykey(self, key, cf_str=None, scf_str=None):
#        if cf_str is None or scf_str is None:
#            return invoke_getbykey(self.socket, key)
#        else:
#            return invoke_getbykey2(self.socket, row_id, cf_str, scf_str)
#            
#    def getlist(self, cf_str):
#        return invoke_getInstacesList(self.socket, cf_str)
        
