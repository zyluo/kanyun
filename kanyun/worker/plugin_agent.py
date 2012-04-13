#!/usr/bin/env python
# encoding: utf-8
# TAB char: space[4]
# Last update: Yuwei Peng<yuwei5@staff.sina.com.cn> 2012-3-28

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

import datetime
import time
from xml.etree import ElementTree

import libvirt
"""
collect info of vm
"""

# add by pyw
class Diff():
    """TODO:same as class Statistics() in server, merge."""
    
    def __init__(self):
        self.first = True
        self.count = 0
        self.previous = 0.0
        self.diff = 0.0
        self.previous_time = time.time()
        self.time_pass = 0
        
    def update(self, value):
        self.count += 1
        if self.first:
            self.first = False
            self.diff = 0.0
            self.previous = value
            self.time_pass = time.time() - self.previous_time
            self.previous_time = time.time()
            return

        self.diff = value - self.previous
        self.previous = value
        self.time_pass = time.time() - self.previous_time
        self.previous_time = time.time()
            
    def get_diff(self):
        return self.diff
        
    def get_time_pass(self):
        return self.time_pass


class LibvirtMonitor(object):

    def __init__(self, uri='qemu:///system'):
        self.conn = libvirt.openReadOnly(uri)
        self.hostname = self.conn.getHostname()
        self.diffs = dict()
        """
        (model, memory_kb, cpus, mhz, nodes,
         sockets, cores, threads) = conn.getInfo()
        """

    def collect_info(self):
        infos_by_dom_name = dict()
        for dom_id in self.conn.listDomainsID():
            dom_conn = self.conn.lookupByID(dom_id)
            dom_key = "%s@%s" % (dom_conn.name(), self.hostname)
            dom_xml = dom_conn.XMLDesc(0)
            # get infos
            infos = list()
            # get domain's cpu, memory info
            infos.extend(self._collect_cpu_mem_info(dom_id, dom_conn))
            # get domain's network info
            nic_devs = self.get_xml_nodes(dom_xml, './devices/interface')
            if not nic_devs:
                # TODO(lzyeval): handle exception
                pass
            for nic_dev in nic_devs:
                infos.extend(self._collect_nic_dev_info(dom_conn, nic_dev))
            # get domain's stroage info
            blk_devs = self.get_xml_nodes(dom_xml, './devices/disk')
            if not blk_devs:
                # TODO(lzyeval): handle exception
                pass
            for blk_dev in blk_devs:
                infos.extend(self._collect_blk_dev_info(dom_conn, blk_dev))
            infos_by_dom_name[dom_key] = infos
        return infos_by_dom_name

    @staticmethod
    def get_utc_sec():
        return time.time()

    @staticmethod
    def get_xml_nodes(dom_xml, path):
        disks = list()
        doc = None
        try:
            doc = ElementTree.fromstring(dom_xml)
        except Exception:
            return disks
        ret = doc.findall(path)
        for node in ret:
            devdst = None
            for child in list(node):#.children:
                if child.tag == 'target':
                    devdst = child.attrib['dev']
            if devdst is None:
                continue
            disks.append(devdst)
#        print 'xml_nodes', disks
        return disks

    def _collect_cpu_mem_info(self, dom_id, dom_conn):
        """Returns tuple of
           (total, utc_time_sec, dom_cpu_time, dom_max_mem_db, dom_memory_kb)
        """
        (dom_run_state, dom_max_mem_kb, dom_memory_kb,
         dom_nr_virt_cpu, dom_cpu_time) = dom_conn.info()
        mem_free = dom_max_mem_kb - dom_memory_kb
        if not dom_run_state:
            # TODO(lzyeval): handle exception
            pass
        timestamp = self.get_utc_sec()
        
        if not self.diffs.has_key(dom_id):
            self.diffs[dom_id] = Diff()
        self.diffs[dom_id].update(dom_cpu_time)
        #%CPU = 100 * cpu_time_diff / (t * nr_cores * 10^9)
        #print "%d * %f / (%d * 1 * %d)" % (100.0, self.diffs[dom_id].get_diff(), self.diffs[dom_id].get_time_pass(), 1e9)
        cpu = 100.0 * self.diffs[dom_id].get_diff() / (self.diffs[dom_id].get_time_pass() * 1 * 1e9)
        print dom_id, 'cpu usage:', cpu, '%, cpu_time:', dom_cpu_time, "mem:", mem_free, "/", dom_max_mem_kb
        # NOTE(lzyeval): libvirt currently can only see total of all vcpu time
#        return [('cpu', 'total', (timestamp, dom_cpu_time)),
#                ('mem', 'total', (timestamp, dom_max_mem_kb, dom_memory_kb))]
        return [('cpu', 'total', (timestamp, cpu)),
                ('mem', 'total', (timestamp, dom_max_mem_kb, mem_free))]

    def _collect_nic_dev_info(self, dom_conn, nic_dev):
        """Returns tuple of
           (nic_dev, utc_time_sec, rx_bytes, tx_bytes)
        """
        (rx_bytes, rx_packets, rx_errs, rx_drop, tx_bytes,
         tx_packets, tx_errs, tx_drop) = dom_conn.interfaceStats(nic_dev)
        timestamp = self.get_utc_sec()
        print "rx=", rx_bytes, "tx=", tx_bytes
        return [('nic', nic_dev, (timestamp, rx_bytes, tx_bytes))]

    def _collect_blk_dev_info(self, dom_conn, blk_dev):
        """Returns tuple of
           (blk_dev, utc_time_sec, rx_bytes, tx_bytes)
        """
        rd_req, rd_bytes, wr_req, wr_bytes, errs = dom_conn.blockStats(blk_dev)
        timestamp = self.get_utc_sec()
        print "r=", rd_bytes, "w=", wr_bytes
        return [('blk', blk_dev, (timestamp, rd_bytes, wr_bytes))]

agent = None
def plugin_call():
    global agent
    if agent is None:
        agent = LibvirtMonitor()
    ret = agent.collect_info()
    return ret
    
    
def plugin_test():
    ret = []
    old_data = None
    agent = LibvirtMonitor()
    for _ in range(60):
        new_data = agent.collect_info()
        if old_data is None:
            # TODO(lzyeval): do something meaningful
            old_data = new_data
        else:
            for dom_name, new_raw_data in new_data.iteritems():
                old_raw_data = old_data.get(dom_name)
                if old_raw_data is None:
                    # TODO(lzyeval): handle exception(?)
                    continue
                all_data = list()
                all_data.extend(old_raw_data)
                all_data.extend(new_raw_data)
                # ['cpu', 'mem', 'net', 'blk', 'blk']
                metrics = dict.fromkeys(map(lambda (x, y, z): x, all_data)).keys()
                # ['cpu', 'mem', 'net', 'blk']
                for _m in metrics:
                    samples = filter(lambda (x, y, z): x == _m, all_data)
                    # if _m == 'cpu'
                    # [('cpu', 'total', (12345.0, 124335235.99), ('cpu', 'total', (12405.0, 123477777.9)]
                    # [('blk', 'vda', (12345.0, 124335235.99), ('blk', 'vdb', (12405.0, 123477777.9),
                    # ('blk', 'vda', (12345.0, 124335235.99), ('blk', 'vdb', (12405.0, 123477777.9)]
                    devs = dict.fromkeys(map(lambda (x, y, z): y,
                                             samples)).keys()
                    # ['vda', 'vdb']
                    for _d in devs:
                        datas = map(lambda(x, y, z): z,
                                    filter(lambda(a, b, c): b == _d, samples))
                        # if _d == 'vda':
                        # [('blk', 'vda', (12345.0, 124335235.99), ('blk', 'vda', (12385.0, 124335235.99))]
                        # TODO(lzyeval): return dict with all data calulated
                        #                with total
                        #print _d, datas
                        ret.append((_d, datas))
                # FIXME(lzyeval): delete me
                break
            old_data.update(new_data)
        time.sleep(1)
        
    return ret
    
    
#if __name__ == '__main__':
#    plugin_test()
