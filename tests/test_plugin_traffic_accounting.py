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
    output = """Chain PREROUTING (policy ACCEPT 24195128 packets, 2563747508 bytes)
    pkts      bytes target     prot opt in     out     source               destination         
   10998  4003272            all  --  *      *       10.0.0.2             0.0.0.0/0           /* instance-00000001 */"""
    return output


class PluginTrafficAccountingTest(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        pass
        
    def tearDown(self):
        self.mox.UnsetStubs()

    def testWorkerClass(self):
        print 'Unit test of worker.'
        self.CMD = "sudo iptables -t raw -nvxL PREROUTING"
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
        self.assertEquals(info['instance-00000001'+plugin_traffic_accounting.hostname][0], '10.0.0.2')


if __name__ == '__main__':
    unittest.main()
