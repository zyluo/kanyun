#!/usr/bin/env python
# encoding: utf-8
# TAB char: space
#
# Author: Lev Givon <lev(at)columbia(dot)edu>
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-19

import sys
import time
import signal
import traceback
import logging
import ConfigParser
import json
import zmq

from kanyun.database.cassadb import CassaDb
import plugin_agent_srv
from kanyun.common.const import *

"""
Save the vm's system info data to db.
protocol:
    http://wiki.sinaapp.com/doku.php?id=monitoring
"""
living_status = dict()


logger = logging.getLogger()
handler = logging.FileHandler("/tmp/kanyun-server.log")
logger.addHandler(handler)
logger.setLevel(logging.NOTSET)
            
class LivingStatus():

    def __init__(self, worker_id = '1'):
        self.min = 2 # 2min
        self.update()
        self.alerted = False
        self.worker_id = worker_id
        self.previous_alert_time = 0
        
    def update(self):
        self.update_time = time.time()
        self.alerted = False
        
    def is_die(self):
        return time.time() - self.update_time > self.min * 60 
        
    def on_die(self):
        ret = 0
        if not self.alerted:
            self.alert_once()
            ret += 1
            
        # each minutes less than once
        if time.time() - self.previous_alert_time > 60: 
            self.alert()
            ret += 1
            
        return ret
        
    ####### private ########
    def alert_once(self):
        # TODO: dispose timeout worker here 
        print '*' * 400
        print '[WARNING]worker', self.worker_id, "is dead. email sendto admin"
        print '*' * 400
        self.alerted = True
        
    def alert(self):
        print '\033[0;31m[WARNING]\033[0mworker', self.worker_id, "is dead. Total=", len(living_status)
        self.previous_alert_time = time.time()


def autotask_heartbeat():
    global living_status
    for worker_id, ls in living_status.iteritems():
        if ls.is_die():
            ls.on_die()


def clean_die_warning():
    global config
    global living_status
    
    new_list = dict()
    i = 0
    for worker_id, ls in living_status.iteritems():
        if not ls.is_die():
            new_list[worker_id] = ls
        else:
            i = i + 1

    living_status = new_list
    print i, "workers cleaned:"
    
    
def list_workers():
    global living_status
    print "-" * 60
    for worker_id, ls in living_status.iteritems():
        print 'worker', worker_id, "update @", ls.update_time
    print len(living_status), "workers."
    
    
def plugin_heartbeat(db, data):
    if data is None or len(data) < 3:
        logger.debug("[ERR]invalid heartbeat data")
        return
    worker_id, update_time, status = data
    if living_status.has_key(worker_id):
        living_status[worker_id].update()
    else:
        living_status[worker_id] = LivingStatus(worker_id)
    logger.debug("heartbeat:%s" % data)
    if 0 == status:
        logger.debug("%s quited" % (worker_id))
        del living_status[worker_id]


def plugin_decoder_agent(db, data):
    if data is None or len(data) <= 0:
        logger.debug('invalid data:%s' % (data))
        return
        
    pass_time = time.time()
    plugin_agent_srv.plugin_decoder_agent(db, data)
    print 'spend \033[1;33m%f\033[0m seconds' % (time.time() - pass_time)
    print '-' * 60
    
    
def plugin_decoder_traffic_accounting(db, data):
    # protocol:{'instance-00000001': ('10.0.0.2', 1332409327, '0')}
    # verify the data
    if data is None or len(data) <= 0:
        logger.debug('invalid data:%s' % (data))
        return
    
    logger.debug('save data:%s' % (data))
    for i in data:
        if len(i) > 0 and len(data[i]) > 2:
            db.insert('vmnetwork', i, {data[i][0]: {data[i][1]: data[i][2]}})


def SignalHandler(sig, id):
    global running
    
    if sig == signal.SIGUSR1:
        list_workers()
    elif sig == signal.SIGUSR2:
        clean_die_warning()
    elif sig == signal.SIGINT:
        running = False


def register_signal():
    signal.signal(signal.SIGUSR1, SignalHandler)
    signal.signal(signal.SIGUSR2, SignalHandler)
    signal.signal(signal.SIGINT, SignalHandler)
   
