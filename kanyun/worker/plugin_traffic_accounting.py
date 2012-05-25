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

import subprocess
import shlex
import time

"""
A worker plugin run in nova-network node, get the network traffic.
Protocol format:
{'10.0.0.2': {'11111': '12'}, '10.0.0.3': {'11122': '45'}}
cf.insert('10.0.0.2', {u'usage': {1332389700: '12'}})

run without root permision:
    sudo touch /etc/sudoers.d/monitor
    sudo vi /etc/sudoers.d/monitor
    sudo chmod 440 /etc/sudoers.d/monitor
    username ALL = (root) NOPASSWD: /sbin/iptables-save, /sbin/iptables

mock:
  for testing only:
     On compute node:
      iptables -t filter -N nova-compute-f-inst-$instance_id
      iptables -I FORWARD -s $instance_ip -j nova-compute-f-inst-$instance_id
      iptables -A nova-compute-f-inst-$instance_id -o $public_interface \
                     -m comment \
                     --comment " $instance_id $instance_ip accounting rule "

      iptables -t filter -N nova-compute-f-inst-112
      iptables -I FORWARD -s 10.0.0.3 -j nova-compute-f-inst-112
      iptables -A nova-compute-f-inst-112 -o eth0 -m comment \
                         --comment " 112 10.0.0.3 accounting rule "
     On load balancer node:
      # TODO(wenjianhn)
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
CMD = "sudo iptables-save -t filter -c"
hostname = get_hostname()

def get_traffic_accounting_info():
    """
    return value format example:{'key': ('ip', time, bytes)}
    {'116@swsdevp': ('10.0.0.95', 1334555143, '0')}
    """
    global _ip_bytes
    
    records = subprocess.check_output(shlex.split(CMD),
                                      stderr=subprocess.STDOUT)
    lines = records.splitlines()[2:]
    acct_records = [line for line in lines if "accounting rule" in line]
    
    ret = dict()

    for record in acct_records:
        out_bytes = record.split()[0].partition(':')[2][0:-1]
        instance_id = record.split()[9] + hostname
        instance_ip = record.split()[10]

        # Is total out bytes(sum of history)
        val = float(out_bytes)

        if instance_id in _ip_bytes:
            prev_out_bytes = _ip_bytes[instance_id]
            val = float(out_bytes) - prev_out_bytes

            if val < 0:
                # error
                print "get_traffic_accounting_info error", float(out_bytes), prev_out_bytes
                val = float(out_bytes)
        else:
            # discard the first value
            val = 0

        # save current value
        _ip_bytes[instance_id] = float(out_bytes)

        ret[instance_id] = (instance_ip, int(time.time()), str(val))

    return ret

if __name__=='__main__':
    import time
    import sys
    interval = 2
    if len(sys.argv) == 2:
        interval = int(sys.argv[1])
    while True:
        for k, info in get_traffic_accounting_info().iteritems():
            print k, info

        time.sleep(interval)
