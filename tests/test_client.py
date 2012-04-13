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
from kanyun.client.api_client import ApiClient


if __name__ == '__main__':
    time.clock()
#    ApiTestSuite = unittest.TestSuite()
#    ApiTestSuite.addTest(StatisticsTest("testStatistics"))
#            
#    runner = unittest.TextTestRunner()
#    runner.run(ApiTestSuite)
    
    client = ApiClient()
    client.period = 1
    client.cf_str = u"cpu"
    client.scf_str = u"total"
    client.time_from = time.time() - 30*24*60*60
    rs = client.getlist(client.cf_str)
    print rs
    for i in rs:
        print '-' * 60
        print "key=", i, ":", 
        r = client.getbykey(i, cf_str = client.cf_str)
        print r
        for i1 in r:
            client.key = i
            client.scf_str = u'10.0.0.2'
            client.time_to = time.time()
            print "sum = ", client.get_sum()
            print "max = ", client.get_max()
            print "min = ", client.get_min()
            print "avg = ", client.get_average()
