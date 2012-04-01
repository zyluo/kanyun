#!/usr/bin/env python
# encoding: utf-8
# TAB char: space
#
# Task worker - design 2
# Adds pub-sub flow to receive and respond to kill signal
#
# Author: Jeremy Avnet (brainsik) <spork(dash)zmq(at)theory(dot)org>
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-19
#

import json
import sys
import time
import zmq
import logging
import ConfigParser

"""
protocol:
    http://wiki.sinaapp.com/doku.php?id=monitoring
"""

WORKER_ID = "black"

class MSG_TYPE:
    """same as server.py"""
    HEART_BEAT = '0'
    LOCAL_INFO = '1'
    TRAFFIC_ACCOUNTING = '2'
    AGENT = '3'

# plugin
def plugin_heartbeat(status = 1):
    """status: 0:I will exit; 1:working"""
    info = [WORKER_ID, time.time(), status]
    return MSG_TYPE.HEART_BEAT, info
    
def plugin_local_cpu():
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

def plugin_traffic_accounting_info():
    import plugin_traffic_accounting
    info = plugin_traffic_accounting.get_traffic_accounting_info()
    if len(info) <= 0:
        return MSG_TYPE.TRAFFIC_ACCOUNTING, {}
    return MSG_TYPE.TRAFFIC_ACCOUNTING, info

def plugin_agent_info():
    import plugin_agent
    info = plugin_agent.plugin_call()
    return MSG_TYPE.AGENT, info
    

class Worker:
    """Get the vm's system info, and send to the server.
    """
    # before the first run ,the rate is 1000(milliseconds). after the first run, rate is 5000(milliseconds)
    working_rate = 1000
    
    def __init__(self, context = None, feedback_host='127.0.0.1', feedback_port=5559, logger = None):
        """ context is zeroMQ socket context"""
        self.plugins = list()
        self.last_work_min = None # this value is None until first update
        self.update_time()
        self.logger = logger
        if self.logger is None:
            self.logger = logging.getLogger()
            handler = logging.FileHandler("/tmp/worker.log")
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.NOTSET)
        if not (context is None):
            self.feedback = context.socket(zmq.PUSH)
            self.feedback.connect("tcp://%s:%s" % (feedback_host, feedback_port))
    
    def clear_plugin(self):
        self.plugins = list()
    def register_plugin(self, plugin):
        self.plugins.append(plugin)
    
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
        self.logger.debug( 'send:%s' % msg )
        self.feedback.send_multipart(msg)
    
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
        self.logger.debug( '%02d:%02d:%02d working...' % (now[3], now[4], now[5]) )

        for plugin in self.plugins:
            msg_type, info = plugin()
            if (not info is None) and len(info) > 0:
                self.send([msg_type, json.dumps(info)])
            #self.send(info)
        
        self.update_time()
        return True
    
running = True

def main(param):
#    if len(sys.argv) <> 2:
#        logging.debug( "usage: python %s [1-3]" % sys.argv[0]
#        sys.exit(0)

#    worker_id = sys.argv[1]
#    if worker_id not in ['1', '2', '3']:
#        logging.debug( "usage: python %s [1-3]" % sys.argv[0]
#        sys.exit(0)
    global WORKER_ID
    
    if len(sys.argv) == 2 and sys.argv[1] == '--help':
        print 'usage:\nuse speical id: worker <id>\nuse id in config file: worker'
        return

    config = ConfigParser.ConfigParser()
    config.read("monitor_worker.conf")
    cfg = dict(config.items('Worker'))
    
    WORKER_ID = cfg['id']
    if len(sys.argv) == 2:
        if len(sys.argv[1]) > 16:
            print 'Invalid worker id.'
            return
        WORKER_ID = sys.argv[1]
    
    logger=logging.getLogger()
    handler=logging.FileHandler("/tmp/worker.log")
    logger.addHandler(handler)
    logger.setLevel(logging.NOTSET)


    running = param
    context = zmq.Context()

    # Socket for control input
    broadcast = context.socket(zmq.SUB)
    broadcast.connect("tcp://%(broadcast_host)s:%(broadcast_port)s" % cfg)
#    broadcast.connect("tcp://localhost:5558")
    broadcast.setsockopt(zmq.SUBSCRIBE, "lb")

    worker = Worker(context=context, feedback_host=cfg['feedback_host'], feedback_port=cfg['feedback_port'], logger=logger)
    # TODO: the plugin come form configure file maybe better
    #worker.register_plugin(plugin_local_cpu)
    worker.register_plugin(plugin_heartbeat)
    worker.register_plugin(plugin_traffic_accounting_info)
    worker.register_plugin(plugin_agent_info)
    # Socket to send messages to
#    feedback = context.socket(zmq.PUSH)
#    feedback.connect("tcp://localhost:5559")

    # Process messages from broadcast
    poller = zmq.Poller()
    poller.register(broadcast, zmq.POLLIN)

    # Process messages from both sockets
    while running:
        socks = dict(poller.poll(worker.working_rate))
        
        # parse the command from server
        if socks.get(broadcast) == zmq.POLLIN:
            msg_type, msg_id, msg_body = broadcast.recv_multipart()
            # Process task
            message = json.loads(msg_body)
            if message['dest'] in ['ALL', worker_id]:
                logger.debug( message['cmd'], message['opt'] )
            # Send results to feedback
            worker.send([msg_type, msg_id,
                                     json.dumps({'worker_id': worker_id,
                                                 'status': 200})])
#            feedback.send_multipart([msg_type, msg_id,
#                                     json.dumps({'worker_id': worker_id,
#                                                 'status': 200})])
    
        # push the info data to server
        worker.info_push()
        
        if not running:
            break
        
        
if __name__ == '__main__':
    main(True)
