#!/usr/bin/env python
# encoding: utf-8
# TAB char: space

import time
import unittest

import mox

import kanyun.worker.plugin_agent as worker

"""A worker plugin run in nova-compute node
"""

SAMPLE_XML = """\
<domain type='kvm' id='10'>
  <name>instance-0000004b</name>
  <uuid>59855752-b62e-37b6-b43a-80ec9104f86a</uuid>
  <memory>4194304</memory>
  <currentMemory>4194304</currentMemory>
  <vcpu>2</vcpu>
  <os>
    <type arch='x86_64' machine='pc-0.14'>hvm</type>
    <kernel>/var/lib/nova/instances/instance-0000004b/kernel</kernel>
    <cmdline>root=/dev/vda console=ttyS0</cmdline>
    <boot dev='hd'/>
  </os>
  <features>
    <acpi/>
  </features>
  <clock offset='utc'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <devices>
    <emulator>/usr/bin/kvm</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/var/lib/nova/instances/instance-0000004b/disk'/>
      <target dev='vda' bus='virtio'/>
      <alias name='virtio-disk0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
    </disk>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='/var/lib/nova/instances/instance-0000004b/disk.local'/>
      <target dev='vdb' bus='virtio'/>
      <alias name='virtio-disk1'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
    </disk>
    <interface type='bridge'>
      <mac address='02:16:3e:37:25:48'/>
      <source bridge='br20'/>
      <target dev='vnet0'/>
      <model type='virtio'/>
      <filterref filter='nova-instance-instance-0000004b-02163e372548'>
        <parameter name='DHCPSERVER' value='192.168.20.1'/>
        <parameter name='IP' value='192.168.20.17'/>
      </filterref>
      <alias name='net0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
    </interface>
    <serial type='file'>
      <source path='/var/lib/nova/instances/instance-0000004b/console.log'/>
      <target port='0'/>
      <alias name='serial0'/>
    </serial>
    <serial type='pty'>
      <source path='/dev/pts/0'/>
      <target port='1'/>
      <alias name='serial1'/>
    </serial>
    <console type='file'>
      <source path='/var/lib/nova/instances/instance-0000004b/console.log'/>
      <target type='serial' port='0'/>
      <alias name='serial0'/>
    </console>
    <input type='mouse' bus='ps2'/>
    <graphics type='vnc' port='5900' autoport='yes' listen='0.0.0.0' keymap='en-us'/>
    <video>
      <model type='cirrus' vram='9216' heads='1'/>
      <alias name='video0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
    </video>
    <memballoon model='virtio'>
      <alias name='balloon0'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0'/>
    </memballoon>
  </devices>
  <seclabel type='dynamic' model='apparmor'>
    <label>libvirt-59855752-b62e-37b6-b43a-80ec9104f86a</label>
    <imagelabel>libvirt-59855752-b62e-37b6-b43a-80ec9104f86a</imagelabel>
  </seclabel>
</domain>\
"""

class TestLibvirtMonitor(unittest.TestCase):

    def setUp(self):
        self.mocker = mox.Mox()
        self.a = worker.LibvirtMonitor()

    def testCall(self):
        info = worker.plugin_call()
        print info
        
class TestLibvirtMonitorMox(unittest.TestCase):

    def setUp(self):
        self.mocker = mox.Mox()
        #self.a = self.mocker.CreateMock(worker.LibvirtMonitor)
        self.a = worker.LibvirtMonitor()

    def test_collect_info(self):
        pass

    def test_get_utc_sec(self):
#        self.a.get_utc_sec(test_a)
        utc_sec = self.a.get_utc_sec()
        self.assertTrue(time.time() - 1 < utc_sec < time.time())

    def test_get_devs(self):
        # make sure the shuffled sequence does not lose any elements
        devs = self.a.get_xml_nodes(SAMPLE_XML, './devices/interface')
        print "devs:", devs
        self.assertEqual(devs, ['vnet0'])
        devs = self.a.get_xml_nodes(SAMPLE_XML, './devices/disk')
        self.assertEqual(devs, ['vda', 'vdb'])

if __name__ == '__main__':
    time.clock()
    AppTestSuite = unittest.TestSuite()
    AppTestSuite.addTest(TestLibvirtMonitorMox("test_get_utc_sec"))
    AppTestSuite.addTest(TestLibvirtMonitor("testCall"))

    
    runner = unittest.TextTestRunner()
    runner.run(AppTestSuite)
