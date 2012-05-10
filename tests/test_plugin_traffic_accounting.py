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

import time
import sys
import unittest
import mox
import subprocess
import shlex
from kanyun.worker import plugin_traffic_accounting

def getHostNameMox():
    return "@host"
    
    
def SubprocessCheckOutputMox():
    output = """# Generated by iptables-save v1.4.10 on Mon Apr 16 07:11:56 2012
*filter
:INPUT ACCEPT [2656:891905]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [2755:344385]
:nova-api-FORWARD - [0:0]
:nova-api-INPUT - [0:0]
:nova-api-OUTPUT - [0:0]
:nova-api-local - [0:0]
:nova-compute-FORWARD - [0:0]
:nova-compute-INPUT - [0:0]
:nova-compute-OUTPUT - [0:0]
:nova-compute-f-inst-1 - [0:0]
:nova-compute-inst-1 - [0:0]
:nova-compute-local - [0:0]
:nova-compute-provider - [0:0]
:nova-compute-sg-fallback - [0:0]
:nova-filter-top - [0:0]
:nova-network-FORWARD - [0:0]
:nova-network-INPUT - [0:0]
:nova-network-OUTPUT - [0:0]
:nova-network-local - [0:0]
[1354358:167161249] -A INPUT -j nova-network-INPUT 
[1345501:164271772] -A INPUT -j nova-compute-INPUT 
[1345501:164271772] -A INPUT -j nova-api-INPUT 
[0:0] -A INPUT -i virbr0 -p udp -m udp --dport 53 -j ACCEPT 
[0:0] -A INPUT -i virbr0 -p tcp -m tcp --dport 53 -j ACCEPT 
[0:0] -A INPUT -i virbr0 -p udp -m udp --dport 67 -j ACCEPT 
[0:0] -A INPUT -i virbr0 -p tcp -m tcp --dport 67 -j ACCEPT 
[86:5160] -A FORWARD -s 10.0.0.2/32 -j nova-compute-f-inst-1 
[51002:1865929] -A FORWARD -j nova-filter-top 
[51002:1865929] -A FORWARD -j nova-network-FORWARD 
[0:0] -A FORWARD -j nova-compute-FORWARD 
[0:0] -A FORWARD -j nova-api-FORWARD 
[0:0] -A FORWARD -d 192.168.122.0/24 -o virbr0 -m state --state RELATED,ESTABLISHED -j ACCEPT 
[0:0] -A FORWARD -s 192.168.122.0/24 -i virbr0 -j ACCEPT 
[0:0] -A FORWARD -i virbr0 -o virbr0 -j ACCEPT 
[0:0] -A FORWARD -o virbr0 -j REJECT --reject-with icmp-port-unreachable 
[0:0] -A FORWARD -i virbr0 -j REJECT --reject-with icmp-port-unreachable 
[1362724:200873262] -A OUTPUT -j nova-filter-top 
[1332367:196687842] -A OUTPUT -j nova-network-OUTPUT 
[1332367:196687842] -A OUTPUT -j nova-compute-OUTPUT 
[1332367:196687842] -A OUTPUT -j nova-api-OUTPUT 
[136:11222] -A nova-api-INPUT -d 192.168.32.8/32 -p tcp -m tcp --dport 8775 -j ACCEPT 
[0:0] -A nova-compute-FORWARD -i br100 -j ACCEPT 
[0:0] -A nova-compute-FORWARD -o br100 -j ACCEPT 
[57:3420] -A nova-compute-f-inst-1 -o br100 -m comment --comment \" 1 10.0.0.2 accounting rule \" 
[0:0] -A nova-compute-inst-1 -m state --state INVALID -j DROP 
[30350:4185000] -A nova-compute-inst-1 -m state --state RELATED,ESTABLISHED -j ACCEPT 
[7:420] -A nova-compute-inst-1 -j nova-compute-provider 
[0:0] -A nova-compute-inst-1 -s 10.0.0.1/32 -p udp -m udp --sport 67 --dport 68 -j ACCEPT 
[7:420] -A nova-compute-inst-1 -s 10.0.0.0/24 -j ACCEPT 
[0:0] -A nova-compute-inst-1 -j nova-compute-sg-fallback 
[30357:4185420] -A nova-compute-local -d 10.0.0.2/32 -j nova-compute-inst-1 
[0:0] -A nova-compute-sg-fallback -j DROP 
[1413726:202739191] -A nova-filter-top -j nova-network-local 
[1413726:202739191] -A nova-filter-top -j nova-compute-local 
[1383369:198553771] -A nova-filter-top -j nova-api-local 
[51002:1865929] -A nova-network-FORWARD -i br100 -j ACCEPT 
[0:0] -A nova-network-FORWARD -o br100 -j ACCEPT 
[8797:2885416] -A nova-network-INPUT -i br100 -p udp -m udp --dport 67 -j ACCEPT 
[2:120] -A nova-network-INPUT -i br100 -p tcp -m tcp --dport 67 -j ACCEPT 
[56:3821] -A nova-network-INPUT -i br100 -p udp -m udp --dport 53 -j ACCEPT 
[2:120] -A nova-network-INPUT -i br100 -p tcp -m tcp --dport 53 -j ACCEPT 
COMMIT
# Completed on Mon Apr 16 07:11:56 2012"""
    return output


class PluginTrafficAccountingTest(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        pass
        
    def tearDown(self):
        self.mox.UnsetStubs()

    def testWorkerClass(self):
        print 'Unit test of worker.'
        self.CMD = "sudo iptables-save -t filter -c"
        self.cmd = shlex.split(self.CMD)
        self.mox.StubOutWithMock(subprocess, 'check_output')
        subprocess.check_output(self.cmd, stderr=subprocess.STDOUT).AndReturn(SubprocessCheckOutputMox())
        self.mox.StubOutWithMock(plugin_traffic_accounting, 'get_hostname')
        plugin_traffic_accounting.get_hostname().AndReturn(getHostNameMox())
        self.mox.ReplayAll()
        
        # TODO: how to mox global var in moudle
        plugin_traffic_accounting.hostname = plugin_traffic_accounting.get_hostname()
        info = plugin_traffic_accounting.get_traffic_accounting_info()
        # {'instance-00000001': ('10.0.0.2', 1333074218, '4003272')}
        print info
        self.mox.VerifyAll()
#        self.assertEquals(info['instance-00000001'+plugin_traffic_accounting.hostname][0], '10.0.0.2')
        self.assertEquals(info['1'+plugin_traffic_accounting.hostname][0], '10.0.0.2')


if __name__ == '__main__':
    unittest.main()
