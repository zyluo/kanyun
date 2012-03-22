#!/usr/bin/env python

import json
import random
import time
import uuid
import zmq

class Client(object):

    def __init__(self, protocol="tcp", host="localhost", port="80"):
        url = "%s://%s:%s" % (protocol, host, port)
        context = zmq.Context()
        self.handler = context.socket(zmq.REQ)
        self.handler.connect(url)

    def __del__(self):
        self.handler.close()

    def send(self, msg_type, msg_id, msg_body):
        self.handler.send_multipart([msg_type, msg_id, json.dumps(msg_body)])
        return self.handler.recv_multipart()

if __name__ == '__main__':
    # Initialize random number generator
    random.seed()

    # Make message
    _msg_type = 'lb'
    _msg_id = str(uuid.uuid1())

    client = Client(protocol='tcp', host='localhost', port='5557')
    """
    _msg_body = {'cmd': 'read_lb_list',
                'dest': random.choice(['ALL', '1', '2', '3']),
                'msg': {'user_name': "demo",
                        'tenant': "demo",
                       }
               }

    ack = client.send(_msg_type, _msg_id, _msg_body)

    print
    print '>', _msg_body
    print '<', ack
    print

    _msg_body = {'cmd': 'read_lb',
                'dest': random.choice(['ALL', '1', '2', '3']),
                'msg': {'user_name': "demo",
                        'tenant': "demo",
                        'load_balancer_id': "myHTTPlb",
                       }
               }
    ack = client.send(_msg_type, _msg_id, _msg_body)

    print
    print '>', _msg_body
    print '<', ack
    print
    """

    _msg_body = {'cmd': 'delete_lb',
                'dest': random.choice(['ALL', '1', '2', '3']),
                'msg': {'user_name': 'demo',
                        'tenant': 'demo',
                        'load_balancer_id': 'myLB',
                        'protocol': 'http',
                        'listen_port': 10101,
                        'instance_port': 9592,
                        'balancing_method': 'round_robin',
                        'health_check_timeout_ms': 5,
                        'health_check_interval_ms': 500,
                        'health_check_target_path': '/',
                        'health_check_fail_count': 2,
                        'instance_uuids': ["a-uuid", "b-uuid", "c-uuid"],
                        'http_server_names': ['www.xxx.com', 'www.yyy.com'],
                       }
               }
    #ack = client.send(_msg_type, _msg_id, _msg_body)
    ack = ''

    print
    print '>', _msg_body
    print '<', ack
    print

    _msg_body = {'cmd': 'create_lb',
                'dest': random.choice(['ALL', '1', '2', '3']),
                'msg': {'user_name': 'demo',
                        'tenant': 'demo',
                        'load_balancer_id': 'myLB',
                        'protocol': 'http',
                        'listen_port': 10101,
                        'instance_port': 9592,
                        'balancing_method': 'round_robin',
                        'health_check_timeout_ms': 5,
                        'health_check_interval_ms': 500,
                        'health_check_target_path': '/',
                        'health_check_fail_count': 2,
                        'instance_uuids': ["681500b4-d08c-4208-83b3-68b2b57c1e23"],
                        'http_server_names': ['www.xxx.com', 'www.yyy.com'],
                       }
               }
    ack = client.send(_msg_type, _msg_id, _msg_body)

    print
    print '>', _msg_body
    print '<', ack
    print

    _msg_body = {'cmd': 'update_lb_config',
                'dest': random.choice(['ALL', '1', '2', '3']),
                'msg': {'user_name': 'demo',
                        'tenant': 'demo',
                        'load_balancer_id': 'myLB',
                        'protocol': 'http',
                        'listen_port': 10101,
                        'instance_port': 9592,
                        'balancing_method': 'round_robin',
                        'health_check_timeout_ms': 5,
                        'health_check_interval_ms': 500,
                        'health_check_target_path': '/',
                        'health_check_fail_count': 2,
                        'instance_uuids': ["681500b4-d08c-4208-83b3-68b2b57c1e23"],
                        'http_server_names': ['www.xxx.com', 'www.yyy.com'],
                       }
               }
    ack = client.send(_msg_type, _msg_id, _msg_body)

    print
    print '>', _msg_body
    print '<', ack
    print


    _msg_body = {'cmd': 'update_lb_instances',
                'dest': random.choice(['ALL', '1', '2', '3']),
                'msg': {'user_name': 'demo',
                        'tenant': 'demo',
                        'load_balancer_id': 'myLB',
                        'protocol': 'http',
                        'listen_port': 10101,
                        'instance_port': 9592,
                        'balancing_method': 'round_robin',
                        'health_check_timeout_ms': 5,
                        'health_check_interval_ms': 500,
                        'health_check_target_path': '/',
                        'health_check_fail_count': 2,
                        'instance_uuids': ["681500b4-d08c-4208-83b3-68b2b57c1e23"],
                        'http_server_names': ['www.xxx.com', 'www.yyy.com'],
                       }
               }
    ack = client.send(_msg_type, _msg_id, _msg_body)

    print
    print '>', _msg_body
    print '<', ack
    print


    _msg_body = {'cmd': 'update_lb_http_server_names',
                'dest': random.choice(['ALL', '1', '2', '3']),
                'msg': {'user_name': 'demo',
                        'tenant': 'demo',
                        'load_balancer_id': 'myLB',
                        'protocol': 'http',
                        'listen_port': 10101,
                        'instance_port': 9592,
                        'balancing_method': 'round_robin',
                        'health_check_timeout_ms': 5,
                        'health_check_interval_ms': 500,
                        'health_check_target_path': '/',
                        'health_check_fail_count': 2,
                        'instance_uuids': ["681500b4-d08c-4208-83b3-68b2b57c1e23"],
                        'http_server_names': ['www.xxx.com', 'www.yyy.com'],
                       }
               }
    ack = client.send(_msg_type, _msg_id, _msg_body)

    print
    print '>', _msg_body
    print '<', ack
    print

    _msg_body = {'cmd': 'read_lb',
                'dest': random.choice(['ALL', '1', '2', '3']),
                'msg': {'user_name': "demo",
                        'tenant': "demo",
                        'load_balancer_id': "myLB",
                       }
               }

    ack = client.send(_msg_type, _msg_id, _msg_body)

    print
    print '>', _msg_body
    print '<', ack
    print
