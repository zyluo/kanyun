#!/usr/bin/env python
# encoding: utf-8
# TAB char: space

import datetime
import time
from xml.etree import ElementTree

import libvirt
"""
db:
+-------------------------------------+
| cf=cpu/mem/...(one item as one cf ) |
+-------------------------------------+---------+
| scf=total/devname                             |
+==============+==============+=======+=========+
|              | col=utc_time | time2 | ...     |
+==============+==============+=======+=========+
| key=instance | val1(subval) | val2  | ...     |
+===============================================+

protocol:

[('cpu', 'total', (utc_time, cpu_time)), 
('mem', 'total', (utc_time, max, free)), 
('nic', 'vnet8', (utc_time, incoming, outgoing(内网))), 
('blk', 'vda', (utc_time, read, write)), 
('blk', 'vdb', (utc_time, read, write))],

(old): {'instance-000000ba@sws-yz-5': 
[('cpu', 'total', (1332400088.149444, 12132270000000L)),  
('mem', 'total', (1332400088.149444, 8388608L, 8388608L)), 
('nic', 'vnet8', (1332400088.152285, 427360746L, 174445810L)), 
('blk', 'vda', (1332400088.156346, 298522624L, 5908590592L)), 
('blk', 'vdb', (1332400088.158202, 2159616L, 1481297920L))], 

(new): {'instance-000000ba@sws-yz-5': 
[('cpu', 'total', (1332400088.149444, 12132270000000L)),  
('mem', 'total', (1332400088.149444, 8388608L, 8388608L)), 
('nic', 'vnet8', (1332400088.152285, 427360746L, 174445810L)), 
('blk', 'vda', (1332400088.156346, 298522624L, 5908590592L)), 
('blk', 'vdb', (1332400088.158202, 2159616L, 1481297920L))], 
"""

class LibvirtMonitor(object):

    def __init__(self, uri='qemu:///system'):
        self.conn = libvirt.openReadOnly(uri)
        self.hostname = self.conn.getHostname()
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
            infos.extend(self._collect_cpu_mem_info(dom_conn))
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
        return disks

    def _collect_cpu_mem_info(self, dom_conn):
        """Returns tuple of
           (total, utc_time_sec, dom_cpu_time, dom_max_mem_db, dom_memory_kb)
        """
        (dom_run_state, dom_max_mem_kb, dom_memory_kb,
         dom_nr_virt_cpu, dom_cpu_time) = dom_conn.info()
        if not dom_run_state:
            # TODO(lzyeval): handle exception
            pass
        timestamp = self.get_utc_sec()
        # NOTE(lzyeval): libvirt currently can only see total of all vcpu time
        return [('cpu', 'total', (timestamp, dom_cpu_time)),
                ('mem', 'total', (timestamp, dom_max_mem_kb, dom_memory_kb))]

    def _collect_nic_dev_info(self, dom_conn, nic_dev):
        """Returns tuple of
           (nic_dev, utc_time_sec, rx_bytes, tx_bytes)
        """
        (rx_bytes, rx_packets, rx_errs, rx_drop, tx_bytes,
         tx_packets, tx_errs, tx_drop) = dom_conn.interfaceStats(nic_dev)
        timestamp = self.get_utc_sec()
        return [('nic', nic_dev, (timestamp, rx_bytes, tx_bytes))]

    def _collect_blk_dev_info(self, dom_conn, blk_dev):
        """Returns tuple of
           (blk_dev, utc_time_sec, rx_bytes, tx_bytes)
        """
        rd_req, rd_bytes, wr_req, wr_bytes, errs = dom_conn.blockStats(blk_dev)
        timestamp = self.get_utc_sec()
        return [('blk', blk_dev, (timestamp, rd_bytes, wr_bytes))]

def plugin_call():
    agent = LibvirtMonitor()
    ret = agent.collect_info()
    return ret
    
def plugin_test():
    ret = []
    old_data = None
    agent = LibvirtMonitor()
    for _ in range(2):
        new_data = agent.collect_info()
        if old_data is None:
            # TODO(lzyeval): do something meaningful
            old_data = new_data
        else:
            for dom_name, new_raw_data in first.iteritems():
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
            old_data.update(first)
        time.sleep(1)
        
    return ret
    
if __name__ == '__main__':
    plugin_test()
