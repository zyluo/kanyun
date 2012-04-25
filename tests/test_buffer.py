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

import unittest
import time
import random
from collections import OrderedDict
from kanyun.common.buffer import HallBuffer

class TestBuffer(unittest.TestCase):

    def setUp(self):
        pass
        
    def tearDown(self):
        pass
    
    def testHallBuffer(self):
        params = ["iphone", 2012]
        data = "detail of 2012 iphone 4S"
        
        b = HallBuffer()
        key = str(params)
        print "Hit rate=", b.get_hit_rate(params), b.get_hit_rate(key), data
        self.assertEqual(b.get_hit_rate(params), 0)
        
        if b.hit_test(key):
            print b.get_buf(key);
        else:
            b.save(key, data)
            print "not hit."
        print "Hit rate=", b.get_hit_rate(params), b.get_hit_rate(key), data
            
        if b.hit_test(key):
            print "hit!"
            print b.get_buf(key);
        else:
            b.save(key, data)
        print "Hit rate=", b.get_hit_rate(params), b.get_hit_rate(key), data
        self.assertEqual(b.get_hit_rate(params), 1)
        
        b.cleanup(time_out = 0)
        print "after cleanup, Hit rate=", b.get_hit_rate(params), data, b.get_hit_rate(key)
        self.assertEqual(b.get_hit_rate(params), 0)


if __name__ == '__main__':
    time.clock()
    ApiTestSuite = unittest.TestSuite()
    ApiTestSuite.addTest(TestBuffer("testHallBuffer"))
    
    runner = unittest.TextTestRunner()
    runner.run(ApiTestSuite)
