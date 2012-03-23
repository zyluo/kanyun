# encoding: utf-8
# TAB char: space
# Task ventilator
# Binds PUSH socket to tcp://localhost:5557
# Sends batch of tasks to workers via that socket
#
# Author: Lev Givon <lev(at)columbia(dot)edu>
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-19

import ConfigParser
import json
import sys
import traceback
import zmq
import db
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
"""

class MSG_TYPE:
    """same as worker.py"""
    LOCAL_INFO = '0'
    TRAFFIC_ACCOUNTING = '1'
    AGENT = '2'

def plugin_decoder_agent(db, data):
    if len(data) <= 0:
        print 'invalid data:', data
        return
        
    plugin_agent_srv.plugin_decoder_agent(db, data)
    
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


def get_work_msg(cmd, **msg):
    res = db.read_whole_lb(**msg)
    if cmd == "delete_lb":
        res = dict(filter(lambda (x, y): x in ['user_name', 'tenant',
                                               'load_balancer_id',
                                               'protocol'], res.items()))
    return res

if __name__ == '__main__':
    # register_plugin
    plugins = {}
    plugins[MSG_TYPE.TRAFFIC_ACCOUNTING] = plugin_decoder_traffic_accounting
    plugins[MSG_TYPE.AGENT] = plugin_decoder_agent
    # 

    config = ConfigParser.ConfigParser()
    config.read("demux.conf")
    server_cfg = dict(config.items('Demux'))

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
            
