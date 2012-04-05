#!/usr/bin/env python
# encoding: utf-8
# TAB char: space
# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-19

import time
import sys
import signal
import ConfigParser
import json
import traceback
import zmq
#import db
import pycassa

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

running = True
living_status = dict()
config = ConfigParser.ConfigParser()

def autotask_heartbeat():
    global config
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
    
    cf = pycassa.ColumnFamily(db, 'vmnetwork')
    print 'save:', data
    for i in data:
        if len(i) > 0 and len(data[i]) > 2:
            # cf.insert('instance-00000001', {'10.0.0.2': {1332409327: '0'}})
            cf.insert(i, {data[i][0]: {data[i][1]: data[i][2]}})


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
    
if __name__ == '__main__':
    # register_plugin
    plugins = dict()
    plugins[MSG_TYPE.HEART_BEAT] = plugin_heartbeat
    plugins[MSG_TYPE.TRAFFIC_ACCOUNTING] = plugin_decoder_traffic_accounting
    plugins[MSG_TYPE.AGENT] = plugin_decoder_agent
    
    # register autotask
    autotasks = list()
    autotasks.append(autotask_heartbeat)
    # 

    config.read("demux.conf")
    server_cfg = dict(config.items('Demux'))
    
    register_signal()

    context = zmq.Context()

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
        try:
            socks = dict(poller.poll(20000))
        except zmq.core.error.ZMQError:
            pass
        
        # parse the command form client
#        if socks.get(handler) == zmq.POLLIN:
#            print 'REQ poolin'
#            msg_type, msg_id, msg_json = handler.recv_multipart()
#            msg_body = json.loads(msg_json)
#            cli_msg = {'code': 200, 'desc': 'OK'}
#            try:
#                cmd = msg_body['cmd']
#                msg = msg_body['msg']
#                print cmd, msg
#                print
#                # access db and get return msg
#                if cmd in ['read_lb', 'read_lb_list', 'read_load_balancer_id_all',
#                           'read_http_server_name_all']:
#                    db_res = getattr(db, cmd)(**msg)
#                    cli_msg.update(db_res)
#                elif cmd in ['create_lb', 'delete_lb', 'update_lb_config',
#                             'update_lb_instances', 'update_lb_http_server_names']:
#                    getattr(db, cmd)(**msg)
#                    work_cmd = "update_lb" if cmd.startswith("update_lb") else cmd
#                    work_msg = get_work_msg(cmd, **msg)
#                    print ">>>>>>>>>", work_msg
#                    print
#                    broadcast.send_multipart([msg_type, msg_id,
#                                              json.dumps({'cmd': work_cmd,
#                                                          'msg': work_msg})])
#                else:
#                    raise Exception("Invalid command")
#            except Exception, e:
#                print traceback.format_exc()
#                cli_msg['code'] = 500
#                cli_msg['desc'] = str(e)
#            print cmd, cli_msg
#            print
#            handler.send_multipart([msg_type, msg_id,
#                                    json.dumps({'cmd': cmd,
#                                                'msg': cli_msg})])

        # parse the data from worker and save to database
        if socks.get(feedback) == zmq.POLLIN:
            try:
                msg_type, report = feedback.recv_multipart()
            except zmq.core.error.ZMQError:
                pass
            
            if plugins.has_key(msg_type) and len(report) > 0:
                report_str = ''.join(report)
                print 'recv(%s):%s' % (msg_type, report_str)
                data = json.loads(report_str)
                plugins[msg_type](data_db, data)
            else:
                print 'invaild data(%s):%s' % (msg_type, report_str)
            
        for task in autotasks:
            task()
