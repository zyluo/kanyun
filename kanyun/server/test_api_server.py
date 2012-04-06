import unittest
import time
import sys
import random
import mox
import pycassa
import api_server

class StatisticsTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()
        
    def testStatistics(self):
        s = api_server.Statistics()
        isum = 0.0
        val = 1
        for i in range(1,11):
            isum += i
            s.update(i)
            print "%02d. value=%02d, sum=%02d, max=%02d, min=%02d, diff=%02d, agerage=%00.f" \
                % (i, i, s.get_sum(), s.get_max(), s.get_min(), s.get_diff(),  s.get_agerage())
            assert s.get_sum() == isum
            assert s.get_max() == i
            assert s.get_min() == 1
            assert s.get_agerage() == isum / i
        print "Statistics test \t[\033[1;33mOK\033[0m]"

def InitApiMox():
    pass
    
class ColumnFamilyMox():
    def __init__(self, a='', b=''):
        pass
    pass
#    return "ColumnFamilyMox"
    
class TestApiServer(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        
    def tearDown(self):
        self.mox.UnsetStubs()

    def testGetCf(self):
        m = self.mox
        self.mox.StubOutWithMock(api_server, 'init_api')
        api_server.init_api().AndReturn(InitApiMox())
        
        self.mox.StubOutWithMock(pycassa, 'ColumnFamily')
        pycassa.ColumnFamily().AndReturn(ColumnFamilyMox())
        pycassa.ColumnFamily('db', 'cpu').AndReturn(ColumnFamilyMox())

        self.mox.ReplayAll()
        api_server.data_db = 'db'
        api_server.init_api()
        api_server.get_cf("cpu")
        api_server.get_cf2("testcf")
        self.mox.VerifyAll()
        
#    
    def test_api_1(self):
        time.clock()
        row_id = 'instance-00000001@pyw.novalocal'
        statistic = api_server.STATISTIC.AVERAGE
        period = 5
        time_from = 1332815400
        time_to = 0
        scf_str = 'total'
        cf_str = 'cpu'
        rs, count, _ = api_server.api_getdata(row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to)
        print "%d results, spend %f seconds" % (count, time.clock())
        print '-' * 60
    
    def test_api_statistic(self):
        time.clock()
        row_id = 'instance-00000001@pyw.novalocal'
        period = 5
        time_from = 1332833464
        time_to = 0
        scf_str = 'total'
        cf_str = 'cpu'
        
        statistic = api_server.STATISTIC.SUM
        rs, count, _ = api_server.api_statistic(row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to)
        print "%d SUM results, spend %f seconds" % (count, time.clock())
        print '-' * 60
        
        statistic = api_server.STATISTIC.MAXIMUM
        rs, count, _ = api_server.api_statistic(row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to)
        print "%d MAXIMUM results, spend %f seconds" % (count, time.clock())
        print '-' * 60
        
        statistic = api_server.STATISTIC.MINIMUM
        rs, count, _ = api_server.api_statistic(row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to)
        print "%d MINIMUM results, spend %f seconds" % (count, time.clock())
        print '-' * 60
        
        statistic = api_server.STATISTIC.AVERAGE
        rs, count, _ = api_server.api_statistic(row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to)
        print "%d AVERAGE results, spend %f seconds" % (count, time.clock())
        print '-' * 60
    def test_demo(self):
        self.assertTrue(True)

    def test_demo2(self):
        self.assertEqual(['vda', 'vdb'], ['vda', 'vdb'])

if __name__ == '__main__':
    time.clock()
    ApiTestSuite = unittest.TestSuite()
    ApiTestSuite.addTest(StatisticsTest("testStatistics"))
    ApiTestSuite.addTest(TestApiServer("testGetCf"))
#    ApiTestSuite.addTest(ApiServerTest("testIsTimeToWorkFirst"))
#    ApiTestSuite.addTest(ApiServerTest("testInfoPush"))
        
    runner = unittest.TextTestRunner()
    runner.run(ApiTestSuite)
