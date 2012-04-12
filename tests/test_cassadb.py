#!/usr/bin/env python
# encoding: utf-8
# TAB char: space
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-28

import unittest
import mox
from kanyun.database import cassadb

class cassadbMox():
    def __init__(self, keyspace='data', ip='127.0.0.1'):
        self.count = 0
    def insert(self, cf_str, key, values):
        pass
    def get_range(self, cf_str):
        pass
    def get(self, cf_str, key, super_column, column_start, column_finish, column_count = 20000):
        pass
    def getbykey(self, cf_str, key):
        pass
    def getbykey2(self, cf_str, key, super_column, column_count):
        pass
    def get_cf(self, cf_str):
        pass

class CassaDBTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()
        
    def ObjectTest(self):
        cf_str = ""
        key = ""
        values = None
        super_column = None
        column_start, column_finish = None, None
        column_count = 0

    def GetTest(self):
        cf_str = "cpu"
        key = "instance-00000001@pyw.novalocal"
        super_column = 'total'
        column_start, column_finish = '', ''
        column_count = 5
        column_reversed = True
        
        pool = pycassa.ConnectionPool('data', server_list=['127.0.0.1'])
        cf = pycassa.ColumnFamily(pool, cf_str)
        rs = cf.get(key=key, super_column=super_column, column_start=column_start, column_finish=column_finish, column_reversed=True, column_count=column_count)
        print rs


if __name__ == '__main__':
    print 'Unit test of worker.'
    DBTestSuite = unittest.TestSuite()
    DBTestSuite.addTest(CassaDBTest("ObjectTest"))
    DBTestSuite.addTest(CassaDBTest("GetTest"))
        
    runner = unittest.TextTestRunner()
    runner.run(DBTestSuite)
