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

        # TODO:how to mox the class?how to mox the constructor func of class?
#        self.mox.StubOutWithMock(db, 'insert')
#        db.insert().AndReturn('')
#    
#        self.mox.StubOutWithMock(cassadb, 'CassaDb')
#        cassadb.CassaDb().AndReturn(cassadbMox())
#        self.mox.ReplayAll()
#        
#        db = cassadb.CassaDb()
#        db.insert(cf_str, key, values)
#        db.get_range(cf_str)
#        db.get(cf_str, key, super_column, column_start, column_finish, column_count = 20000)
#        db.getbykey(cf_str, key)
#        db.getbykey2(cf_str, key, super_column, column_count)
#        db.get_cf(cf_str)
        self.mox.VerifyAll()

if __name__ == '__main__':
    print 'Unit test of worker.'
    DBTestSuite = unittest.TestSuite()
    DBTestSuite.addTest(CassaDBTest("ObjectTest"))
        
    runner = unittest.TextTestRunner()
    runner.run(DBTestSuite)
