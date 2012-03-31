import unittest
import time
import sys
import mox
import zmq
import worker
from worker import Worker

def PluginTrafficAccountingInfoMox():
    info  = {'instance-00000001': ('10.0.0.2', 1332409327, '0')}
    return worker.MSG_TYPE.TRAFFIC_ACCOUNTING, info

def PluginAgentInfo():
    info = {'instance-000000ba@sws-yz-5': 
        [('cpu', 'total', (1332400088.149444, 12132270000000L)), 
        ('mem', 'total', (1332400088.149444, 8388608L, 8388608L)), 
        ('nic', 'vnet8', (1332400088.152285, 427360746L, 174445810L)), 
        ('blk', 'vda', (1332400088.156346, 298522624L, 5908590592L)),  
        ('blk', 'vdb', (1332400088.158202, 2159616L, 1481297920L))]}

    return worker.MSG_TYPE.AGENT, info



class ZmqPollerMox():
    def register(self, p1, p2):
        pass
    def poll(self, p1):
        return dict()
        
class ZmqContextMox():
    def socket(self, mode = zmq.SUB):
        return ZmqContextSocketMox()
class ZmqContextSocketMox():
    def connect(self, conn_str):
        print 'connect', conn_str
        pass
    def setsockopt(self, para1, para2):
        pass
    def send_multipart(self, msg):
        print "send", msg

class WorkerTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()
            
    def testIsTimeToWorkFirst(self):
        # test the first run
        w = worker.Worker()
        t = time.gmtime(time.mktime((2012, 10, 1, 15, 26,0,0,0,0)))
        self.mox.StubOutWithMock(time, 'localtime')
        time.localtime().AndReturn(t)
        self.mox.ReplayAll()
        print 
        print "mox localtime:", time.localtime()
        print
        
        # first and not in worktime
        t = time.gmtime(time.mktime((2012, 10, 1, 15, 26,40,0,0,0)))
        w.last_work_min = None
        ret = w.is_timeto_work()
        assertEqual(ret, False)
        assertFalse(self.last_work_min, None)
                
        # first and in worktime
        t = time.gmtime(time.mktime((2012, 10, 1, 15, 26,0,0,0,0)))
        w.last_work_min = None
        ret = w.is_timeto_work()
        assertEqual(ret, True)
        assertFalse(self.last_work_min, None)
        
        self.mox.VerifyAll()

#    def testIsTimeToWork(self):
#        self.mox.ReplayAll()
#        w = worker.Worker()
#        w.last_work_min = 5
#        now_sec = time.localtime().tm_sec# 5
#        ret = w.is_timeto_work()
#        self.mox.VerifyAll()
#        if now_sec >= 0 and now_sec <= 5 and ret:
#            print 'IsTimeToWork OK'
#    
#    def testInfoPush(self):
#        w = worker.Worker()
#        w.register_plugin(PluginTrafficAccountingInfoMox)
#        w.register_plugin(PluginAgentInfo)
#    
#        t = time.gmtime(time.mktime((2012, 10, 1, 15, 26,0,0,0,0)))
#        self.mox.StubOutWithMock(time, 'localtime')
#        time.localtime().AndReturn(t)
#        #time.localtime().tm_sec.AndReturn(time.mktime())

#        self.mox.ReplayAll()
#        print "testInfoPush:"
#        print "localtime=", time.localtime()
#        self.assertTrue(time.localtime().tm_sec is None)
#        print "sec=" , time.localtime().tm_sec
#        w.info_push()
#        self.mox.VerifyAll()

#        if now_sec >= 0 and now_sec <= 5 and ret:
#            print 'IsTimeToWork OK'
#            
#    def testWorkerClass(self):
#        m = self.mox
#        m.StubOutWithMock(zmq, 'Poller')
#        m.StubOutWithMock(zmq, 'Context')
#        zmq.Context().AndReturn(ZmqContextMox())
#        zmq.Poller().AndReturn(ZmqPollerMox())
#        self.mox.StubOutWithMock(worker, 'plugin_traffic_accounting_info')
#        self.mox.StubOutWithMock(worker, 'plugin_agent_info')
#        worker.plugin_traffic_accounting_info().AndReturn(PluginTrafficAccountingInfoMox())
#        worker.plugin_agent_info().AndReturn(PluginAgentInfo())
#        
#        t = time.gmtime(time.mktime((2012, 10, 1, 15, 26,0,0,0,0)))
#        m.StubOutWithMock(time, 'localtime')
#        # Record a call to 'now', and have it return the value '1234'
#        time.localtime().AndReturn(t)
#        self.mox.ReplayAll()
#        worker.main(False)
#        self.mox.VerifyAll()
#        
#    def test2(self):
#        
#        pass
    
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
    unittest.main()
