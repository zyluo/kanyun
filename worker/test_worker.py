import unittest
import time
import sys
from worker import Worker

class TestWorker(unittest.TestCase):
    def setUp(self):
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
