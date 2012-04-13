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

import time

import plugin_agent

"""
CPU Calculation

http://people.redhat.com/~rjones/virt-top/faq.html#calccpu

How do I calculate %CPU in my own libvirt programs?

Simple %CPU usage for a domain is calculated by sampling virDomainGetInfo
periodically and looking at the virDomainInfo cpuTime field.
This 64 bit field counts nanoseconds of CPU time used by the domain
since the domain booted.

Let t be the number of seconds between samples.
(Make sure that t is measured as accurately as possible,
using something like gettimeofday(2) to measure the real sampling interval).

Let cpu_time_diff be the change in cpuTime over this time,
which is the number of nanoseconds of CPU time used by the domain, ie:

cpu_time_diff = cpuTime(now) - cpuTime(t) seconds ago

Let nr_cores be the number of processors (cores) on the system.
Use virNodeGetInfo to get this.

Then, %CPU used by the domain is:

%CPU = 100 * cpu_time_diff / (t * nr_cores * 10e9)

Because sampling doesn't happen instantaneously,
this can be greater than 100%.
This is particularly a problem where you have many domains and
you have to make a virDomainGetInfo call for each one.
"""

if __name__=='__main__':
    archive = None
    agent = plugin_agent.LibvirtMonitor()
    for _ in range(5):
        first = agent.collect_info()
        if archive is None:
            # TODO(lzyeval): do something meaningful
            archive = first
        else:
            for dom_name, bb in first.iteritems():
                aa = archive.get(dom_name)
                if bb is None:
                    # TODO(lzyeval): handle exception(?)
                    continue
                asdf = list()
                asdf.extend(aa)
                asdf.extend(bb)
                metrics = dict.fromkeys(map(lambda (x, y, z): x, asdf)).keys()
                for _m in metrics:
                    samples = filter(lambda (x, y, z): x == _m, asdf)
                    devs = dict.fromkeys(map(lambda (x, y, z): y,
                                             samples)).keys()
                    for _d in devs:
                        datas = map(lambda(x, y, z): z,
                                    filter(lambda(a, b, c): b == _d, samples))
                        # TODO(lzyeval): return dict with all data calulated
                        #                with total
                        print _d, datas
                # FIXME(lzyeval): delete me
                break
            archive.update(first)
        time.sleep(10)
    """
    print get_nova_instance_id(dom.name()), timestamp
    print 'instance_id:', get_nova_instance_id(dom.name())
    print 'cpu usage:', 1.0e-7 * dom_cpu_time / cpus
    print 'memory usage:', ((dom_max_mem_kb - dom_memory_kb) *
                            1.0e-7 / dom_max_mem_kb)
    """

