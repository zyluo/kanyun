#!/usr/bin/env python
# encoding: utf-8
# TAB char: space
# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-19

import sys
import time
import signal
import traceback
import ConfigParser
import json
import zmq

from kanyun.database.cassadb import CassaDb
import plugin_agent_srv

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
"""

class MSG_TYPE:
    """same as worker.py"""
    HEART_BEAT = '0'
    LOCAL_INFO = '1'
    TRAFFIC_ACCOUNTING = '2'
    AGENT = '3'

living_status = dict()

def autotask_heartbeat():
    global living_status
    for worker_id, update_time in living_status.iteritems():
        if time.time() - update_time > 2 * 60: # 2min
            # TODO: dispose timeout worker here 
            print '\033[0;31m[WARNING]\033[0mworker', worker_id, "is dead. Total=", len(living_status)
          
def clear_die_warning():
    global config
    global living_status
    
    new_list = dict()
    i = 0
    for worker_id, update_time in living_status.iteritems():
        if time.time() - update_time > 2 * 60: # 2min
            new_list[worker_id] = update_time
            i = i + 1

    living_status = new_list
    print i, "workers cleared:"
    
def list_workers():
    global living_status
    print "-" * 60
    for worker_id, update_time in living_status.iteritems():
        print 'worker', worker_id, "update @", update_time
    print len(living_status), "workers."
    
def plugin_heartbeat(db, data):
    if len(data) < 3:
        print "[ERR]invalid heartbeat data"
        return
    worker_id, update_time, status = data
    living_status[worker_id] = time.time()
    print "heartbeat:", data
    if 0 == status:
        print worker_id, "quited."
        del living_status[worker_id]

def plugin_decoder_agent(db, data):
    if len(data) <= 0:
        print 'invalid data:', data
        return
        
    pass_time = time.time()
    plugin_agent_srv.plugin_decoder_agent(db, data)
    print 'spend \033[1;33m%f\033[0m seconds' % (time.time() - pass_time)
    print '-' * 60
    
def plugin_decoder_traffic_accounting(db, data):
    # verify the data
    # protocol:{'instance-00000001': ('10.0.0.2', 1332409327, '0')}
    if len(data) <= 0:
        print 'invalid data:', data
        return
    
#    cf = pycassa.ColumnFamily(db, 'vmnetwork')
    print 'save:', data
    for i in data:
        if len(i) > 0 and len(data[i]) > 2:
            # cf.insert('instance-00000001', {'10.0.0.2': {1332409327: '0'}})
#            cf.insert(i, {data[i][0]: {data[i][1]: data[i][2]}})
            db.insert('vmnetwork', i, {data[i][0]: {data[i][1]: data[i][2]}})


#def get_work_msg(cmd, **msg):
#    res = db.read_whole_lb(**msg)
#    if cmd == "delete_lb":
#        res = dict(filter(lambda (x, y): x in ['user_name', 'tenant',
#                                               'load_balancer_id',
#                                               'protocol'], res.items()))
#    return res

def SignalHandler(sig, id):
    global running
    
    if sig == signal.SIGUSR1:
        list_workers()
    elif sig == signal.SIGUSR2:
        clear_die_warning()
    elif sig == signal.SIGINT:
        running = False

def register_signal():
    signal.signal(signal.SIGUSR1, SignalHandler)
    signal.signal(signal.SIGUSR2, SignalHandler)
    signal.signal(signal.SIGINT, SignalHandler)
   
