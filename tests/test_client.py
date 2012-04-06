#!/usr/bin/env python
# encoding: utf-8
# TAB char: space
#
# Author: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-27
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-28

import time

from kanyun.server.api_client import ApiClient


if __name__ == '__main__':
    client = ApiClient()
    client.period = 1
    client.cf_str = "vmnetwork"
    client.scf_str = "total"
    client.time_from = time.time() - 30*24*60*60
    rs = client.getlist(client.cf_str)
    print rs
    for i in rs:
        print '-' * 60
        print "key=", i, ":", 
        r = client.getbykey(i, cf_str = client.cf_str)
        print r
#        if not r is None: print len(r)
        for i1 in r:
            client.key = i
            client.scf_str = '10.0.0.2'
            client.time_to = time.time()
            print "sum = ", client.get_sum()
            print "max = ", client.get_max()
            print "min = ", client.get_min()
            print "avg = ", client.get_average()
