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
import sys
import random
import mox
import pycassa
from collections import OrderedDict

from kanyun.server.data_server import *


class TestLivingStatus(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        
    def tearDown(self):
        self.mox.UnsetStubs()
    
    def testLivingStatusFunc(self):
        time.clock()
        ls = LivingStatus()
        print 'living'
        ls.update()
        self.assertTrue(not ls.is_die())
        while not ls.is_die():
            now = time.localtime()
            sys.stdout.write("\r%02d:%02d:%02d waitting for die" % 
                                (now.tm_hour, now.tm_min, now.tm_sec))
            sys.stdout.flush()
            time.sleep(1)
        print
        print 'first event:'
        ret = ls.on_die()
        self.assertTrue(ret == 2)
        print 'next event:'
        ret = ls.on_die()
        self.assertTrue(ret == 1)
        print "LivingStatus test \t[\033[1;33mOK\033[0m]"
    
    
class TestDataServer(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        
    def tearDown(self):
        self.mox.UnsetStubs()
    
    def testDataServerFunc(self):
        time.clock()
        db = None
        data = None
        autotask_heartbeat()
        clean_die_warning()
        list_workers()
        plugin_heartbeat(db, data)
        plugin_decoder_agent(db, data)
        plugin_decoder_traffic_accounting(db, data)
        print "DataServerFunc test \t[\033[1;33mOK\033[0m]"


if __name__ == '__main__':
    time.clock()
    ApiTestSuite = unittest.TestSuite()
    ApiTestSuite.addTest(TestLivingStatus("testLivingStatusFunc"))
    ApiTestSuite.addTest(TestDataServer("testDataServerFunc"))

    
    runner = unittest.TextTestRunner()
    runner.run(ApiTestSuite)
