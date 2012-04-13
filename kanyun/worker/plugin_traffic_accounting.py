#!/usr/bin/env python
# encoding: utf-8
# TAB char: space[4]
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

import subprocess
import shlex
import time

"""
A worker plugin run in nova-network node, get the network traffic.
Protocol format:
{'10.0.0.2': {'11111': '12'}, '10.0.0.3': {'11122': '45'}}
cf.insert('10.0.0.2', {u'usage': {1332389700: '12'}})

request:
sudo iptables -t raw -A PREROUTING -s $instance_ip -m comment --comment "instance_id"
sudo iptables -t raw -I PREROUTING -s 10.0.0.3 -m comment --comment "instance-0000003e"

"""

def get_hostname():
    CMD_HOST = "uname -a"
    buf = subprocess.check_output(shlex.split(CMD_HOST), stderr=subprocess.STDOUT)
    buf = buf.split()
    if len(buf) > 1:
        ret = '@' + buf[1]
    else:
        ret = ''
    return ret
    
_ip_bytes = {} # {'10.0.0.2': '10', '10.0.0.3': '5'}
CMD = "sudo iptables -t raw -nvxL PREROUTING"
hostname = get_hostname()

def get_traffic_accounting_info():
    """
    return value format example:
    {'instance-00000001': ('10.0.0.2', 1332409327, '0')}
    """
    
    records = subprocess.check_output(shlex.split(CMD), stderr=subprocess.STDOUT)
    lines = records.splitlines()[2:]
    ret = {}
   
    for line in lines:
        counter_info = line.split()
#        print "line:", line, "counter_info:", counter_info
        out_bytes = counter_info[1]
        instance_ip = counter_info[6]
        instance_id = counter_info[9] + hostname
        val = int(out_bytes)

        if instance_id in _ip_bytes:
            prev_out_bytes = _ip_bytes[instance_id]
            val = int(out_bytes) - prev_out_bytes

            if val < 0:
                val = int(out_bytes)
        else:
            val = int(out_bytes)

        _ip_bytes[instance_id] = int(out_bytes)

        ret[instance_id] = (instance_ip, int(time.time()), str(val))

    return ret

if __name__=='__main__':
    while True:
        print get_traffic_accounting_info()
        import time
        time.sleep(2)
