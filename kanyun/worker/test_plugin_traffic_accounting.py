import time
import sys
import unittest
import mox
import plugin_traffic_accounting
import subprocess
import shlex

def SubprocessCheckOutputMox():
    output = """Chain PREROUTING (policy ACCEPT 24195128 packets, 2563747508 bytes)
    pkts      bytes target     prot opt in     out     source               destination         
   10998  4003272            all  --  *      *       10.0.0.2             0.0.0.0/0           /* instance-00000001 */"""
    return output

class PluginTrafficAccountingTest(unittest.TestCase):
    def setUp(self):
        print 'Unit test of worker.'
        self.CMD = "sudo iptables -t raw -nvxL PREROUTING"
        self.cmd = shlex.split(self.CMD)
        self.mox = mox.Mox()
#        print self.cmd
        self.mox.StubOutWithMock(subprocess, 'check_output')
        subprocess.check_output(self.cmd, stderr=subprocess.STDOUT).AndReturn(SubprocessCheckOutputMox())

    def tearDown(self):
        self.mox.UnsetStubs()

    def testWorkerClass(self):
        self.mox.ReplayAll()
        info = plugin_traffic_accounting.get_traffic_accounting_info()
        # {'instance-00000001': ('10.0.0.2', 1333074218, '4003272')}
        self.mox.VerifyAll()
        self.assertEquals(info['instance-00000001'][0], '10.0.0.2')

if __name__ == '__main__':
    unittest.main()
