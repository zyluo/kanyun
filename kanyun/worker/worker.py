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

import json
import sys
import time
import signal
import zmq
import logging
import traceback
import ConfigParser

from kanyun.common.app import *
from kanyun.common.const import *
"""
protocol:
    http://wiki.sinaapp.com/doku.php?id=monitoring
"""

# plugin
def plugin_heartbeat(worker_id, status=1):
    """status: 0:I will exit; 1:working"""
    info = [worker_id, time.time(), status]
    return MSG_TYPE.HEART_BEAT, info
    
    
def plugin_local_cpu(worker_id):
    # FIXME:how to use import smart?
    """
    Data format:
[{'cpu': '5%'}]
    """
    import subprocess
    import random
    cmd = "sleep %d;top -n 1 -b|grep Cpu|awk '{print $2}'" % (random.randint(0,30))
    ret = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, close_fds=True)
    info = ret.stdout.readlines()
    return MSG_TYPE.LOCAL_INFO, [{"cpu": ''.join(info)}]


def plugin_traffic_accounting_info(worker_id):
    import plugin_traffic_accounting
    info = plugin_traffic_accounting.get_traffic_accounting_info()
    if len(info) <= 0:
        return MSG_TYPE.TRAFFIC_ACCOUNTING, {}
    return MSG_TYPE.TRAFFIC_ACCOUNTING, info


def plugin_agent_info(worker_id):
    import plugin_agent
    info = plugin_agent.plugin_call()
    return MSG_TYPE.AGENT, info
    

class Worker:
    """Get the vm's system info, and send to the server.
    """
    # before the first run ,the rate is 1000(milliseconds). after the first run, rate is 5000(milliseconds)
    working_rate = 1000
    
    def __init__(self, context=None, feedback_host='127.0.0.1', 
                 feedback_port=5559, worker_id=None):
        """ context is zeroMQ socket context"""
        self.plugins = list()
        self.last_work_min = None # this value is None until first update
        self.update_time()
        self.app = App(conf="kanyun.conf")
        self.logger = self.app.get_logger()
        self.cfg = self.app.get_cfg('worker')
        server_host = '127.0.0.1'
        server_port = "5551"
        self.worker_id = worker_id
        
        if worker_id is None and self.cfg.has_key('id'):
            self.worker_id = self.cfg['id']
        if self.cfg.has_key('dataserver_host'):
            server_host = self.cfg['dataserver_host']
        if self.cfg.has_key('dataserver_port'):
            server_port = self.cfg['dataserver_port']
            
        context = zmq.Context()
        self.socket = context.socket(zmq.PUSH)
        self.socket.connect("tcp://%s:%s" % (server_host, server_port))
        print "server is %s:%s" % (server_host, server_port)
    
    def clear_plugin(self):
        self.plugins = list()
        
    def register_plugin(self, plugin):
        self.plugins.append((plugin, True))
    
    def update_time(self):
        """[private]save the current time.First update will between 0-5(sec) in current minutes"""
        localtime = time.localtime()
        if self.last_work_min is None:
            if localtime.tm_sec >= 0 and localtime.tm_sec <= 5:
                self.last_work_min = localtime.tm_min - 1
                if self.last_work_min < 0:
                    self.last_work_min = 59
                self.working_rate = 5000
        else:
            self.last_work_min = localtime.tm_min
            
    def send(self, msg):
        """PUSH the msg(msg is a list)"""
        self.logger.debug('send:%s' % msg)
        self.socket.send_multipart(msg)
    
    def get_leaving_time(self):
        """return leaving seconds before next work time"""
        ret = 60 - time.localtime().tm_sec
        return ret
        
    def is_timeto_work(self):
        """[private]update the time and return if is timeto work
        1.if this minutes does not work, return true else return false.
        note: 
        First run will between xx:xx:00-xx:xx:05, 
        if time is not in this range, will return false"""
        if self.last_work_min is None:
            self.update_time()

        if self.last_work_min is None:
            return False
        return self.last_work_min <> time.localtime().tm_min
        
    def info_push(self):
        """Do the work: if is time to work ,get and send the vms's sysinfo"""
        if not self.is_timeto_work():
            return False
        now = time.localtime()
        self.logger.debug('%02d:%02d:%02d working...' % (now[3], now[4], now[5]))

        for (plugin, enable) in self.plugins:
            try:
                msg_type, info = plugin(self.worker_id)
                if (not info is None) and len(info) > 0:
                    self.send([msg_type, json.dumps(info)])
            except:
                traceback.print_exc()
                enable = False
        
        self.update_time()
        return True
        
    def end(self):
        info = [self.worker_id, time.time(), 0]
        self.send(MSG_TYPE.HEART_BEAT, 0, json.dumps(info))
    

