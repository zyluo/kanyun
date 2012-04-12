#!/usr/bin/env python
# encoding: utf-8
# TAB char: space
#
# test worker
#
# Author: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-19
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-31
#

import unittest
import time
import sys
import json
import mox
from kanyun.worker.worker import Worker
from kanyun.worker.worker import MSG_TYPE


def PluginTrafficAccountingInfoMox(worker_id):
    info  = {'instance-00000001': ('10.0.0.2', 1332409327, '0')}
    return MSG_TYPE.TRAFFIC_ACCOUNTING, info


def PluginAgentInfo(worker_id):
    info = {'instance-000000ba@sws-yz-5': 
        [('cpu', 'total', (1332400088.149444, 12132270000000L)), 
        ('mem', 'total', (1332400088.149444, 8388608L, 8388608L)), 
        ('nic', 'vnet8', (1332400088.152285, 427360746L, 174445810L)), 
        ('blk', 'vda', (1332400088.156346, 298522624L, 5908590592L)),  
        ('blk', 'vdb', (1332400088.158202, 2159616L, 1481297920L))]}

    return MSG_TYPE.AGENT, info


class ZmqPollerMox():

    def register(self, p1, p2):
        pass
        
    def poll(self, p1):
        return dict()
        
class ZmqContextMox():

    def socket(self, mode):
        return ZmqContextSocketMox()
        
        
class ZmqContextSocketMox():

    def __init__(self):
        self.count = 0
        
    def connect(self, conn_str):
        print 'connect', conn_str
        pass
        
    def setsockopt(self, para1, para2):
        pass
        
    def send_multipart(self, msg):
        print "send", msg
        self.count += len(msg)

class WorkerTest(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()
    
    def testWorkerID(self):
        w = Worker(worker_id = 'TestID')
        assert(w.worker_id == 'TestID')
        print "worker_id test \t[\033[1;33mOK\033[0m]"
        
    def testPlugin(self):
        w = Worker()
        w.register_plugin(PluginTrafficAccountingInfoMox)
        w.register_plugin(PluginAgentInfo)
        assert len(w.plugins) == 2
        w.clear_plugin()
        assert len(w.plugins) == 0
        print "Plugin test \t[\033[1;33mOK\033[0m]"
            
    def testIsTimeToWorkFirst(self):
        # test the first run
        w = Worker()
        self.mox.ReplayAll()
        
        # first and not in worktime
        t = time.gmtime(time.mktime((2012, 10, 1, 15, 26,40,0,0,0)))
        w.last_work_min = None
        istime = False
        while istime == False:
            now = time.localtime()
            istime = w.is_timeto_work()
            if not istime:
                ret = w.get_leaving_time()
                sys.stdout.write("\r%02d:%02d:%02d waitting %d seconds for the test of IsTimeToWork  \r" % 
                                (now.tm_hour, now.tm_min, now.tm_sec, ret))
                assert ret == 60 - now.tm_sec
                sys.stdout.flush()
                time.sleep(1)
        print
        
        assert now.tm_sec >=0 and now.tm_sec <= 5
        assert istime == True
        assert not w.last_work_min is None
        
        self.mox.VerifyAll()
        print "update_time test \t[\033[1;33mOK\033[0m]"
        print "is_timeto_work test \t[\033[1;33mOK\033[0m]"
        print "get_leaving_time test \t[\033[1;33mOK\033[0m]"

    def testSend(self):
        self.mox.ReplayAll()
        w = Worker(context = ZmqContextMox())
        msg = [1, json.dumps(["1", {86:2012}])]
        w.send(msg)
        assert w.feedback.count == len(msg)
        self.mox.VerifyAll()
        print "send test \t[\033[1;33mOK\033[0m]"
        
    def testInfoPush(self):
        self.mox.ReplayAll()
        w = Worker(context = ZmqContextMox())
        w.register_plugin(PluginTrafficAccountingInfoMox)
        w.register_plugin(PluginAgentInfo)
        w.info_push()
        self.mox.VerifyAll()
        print "info_push test \t[\033[1;33mOK\033[0m]"
      
class WorkerIntegrationTest():
#class WorkerIntegrationTest(unittest.TestCase):

    def setUp(self):
        print 'Integration test of worker.'
        pass

    def test_istime_to_work(self):
        w = Worker(None)
        
        for _ in range(135):
            time.sleep(w.working_rate)
            now = time.localtime()
            istime = w.is_timeto_work()
            if not istime:
                ret = w.get_leaving_time()
                sys.stdout.write(("\r%02d:%02d:%02d waitting %d seconds for work(last=%d,rate=%d,istime=%s)" % 
                                (now.tm_hour, now.tm_min, now.tm_sec
                                , ret
                                , w.last_work_min
                                , w.working_rate
                                , istime)))
                sys.stdout.flush()
                continue
            print
            sys.stdout.write('%02d:%02d:%02d start fake working.' % 
                            (now[3], now[4], now[5]))
            for __ in range(random.randint(0,60)):
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(1)
            now = time.localtime()
            print '\n%02d:%02d:%02d working success finished.' % (now[3], now[4], now[5])
            w.update_time()
            
            #if only test the first working timepoint, break here.
            #break


if __name__ == '__main__':
    print 'Unit test of worker.'
    WorkerTestSuite = unittest.TestSuite()
    WorkerTestSuite.addTest(WorkerTest("testWorkerID"))
    WorkerTestSuite.addTest(WorkerTest("testPlugin"))
    WorkerTestSuite.addTest(WorkerTest("testSend"))
    WorkerTestSuite.addTest(WorkerTest("testIsTimeToWorkFirst"))
    WorkerTestSuite.addTest(WorkerTest("testInfoPush"))
    
    runner = unittest.TextTestRunner()
    runner.run(WorkerTestSuite)


