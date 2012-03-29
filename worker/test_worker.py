import unittest
import time
import sys
import mox
import zmq
import worker
from worker import Worker

class zmq_Poller_mox():
    def register(self, p1, p2):
        pass
    def poll(self, p1):
        return dict()
        
class zmq_Context_mox():
    def socket(self, mode = zmq.SUB):
        print 'socket'
        return xxx()
class xxx():
    def connect(self, conn_str):
        print 'connect'
        pass
    def setsockopt(self, para1, para2):
        pass

class WorkerTest(unittest.TestCase):
    def setUp(self):
        print 'Unit test of worker.'
        self.mox = mox.Mox()
        m = self.mox
        m.StubOutWithMock(zmq, 'Poller')
        m.StubOutWithMock(zmq, 'Context')
        zmq.Context().AndReturn(zmq_Context_mox())
        zmq.Poller().AndReturn(zmq_Poller_mox())
#        zmq.Context().AndReturn(1234)
#        m.ReplayAll()
#        print datetime.datetime.now()
#        # Verify the time was actually checked.
#        m.VerifyAll()
#        self.context = self.mox.CreateMock(zmq.Context)
    def tearDown(self):
        self.mox.UnsetStubs()

    def testWorkerClass(self):
#        self.feedback = self.context.socket(zmq.PUSH)
#        self.feedback.connect("tcp://127.0.0.1:5559")
        
#        self.broadcast = self.context.socket(zmq.SUB)
#        self.broadcast.connect("tcp://localhost:5558")
#        self.broadcast.setsockopt(zmq.SUBSCRIBE, "lb")
#        
#        self.poller = zmq.Poller()
#        self.poller.register(self.broadcast, zmq.POLLIN)
    
        self.mox.ReplayAll()
        #self.worker = Worker(self.context)
        worker.main()
        self.mox.VerifyAll()

#    def testCreatePersonWithDbException(self):
#        test_person = 'pyw'
#        self.dao.InsertPerson(test_person).AndRaise(PersistenceException('Snakes!'))
#        self.mox.ReplayAll()
#        self.assertRaises(BusinessException, self.manager.CreatePerson, test_person, 'stevepm')
#        self.mox.VerifyAll()
    
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

    def test_demo(self):
        self.assertTrue(True)

    def test_demo2(self):
        self.assertEqual(['vda', 'vdb'], ['vda', 'vdb'])

if __name__ == '__main__':
    unittest.main()
