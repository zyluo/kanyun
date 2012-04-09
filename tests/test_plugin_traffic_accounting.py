#!/usr/bin/env python
# encoding: utf-8
# TAB char: space
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-28

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
