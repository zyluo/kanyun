#!/usr/bin/env python
# encoding: utf-8
# TAB char: space

# Author: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-27
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-28

import pycassa

def a():
    pass

def tmp():
    pass

class CassaDb():
    def __init__(self, keyspace, ip):
        """
        # self.cfs:
        # ColumnFamilys object collection
        # data format: {key: ColumnFamily Object}
        # example: {'cpu', ColumnFamily()}
        """
        self.cfs = dict()
        self.db = pycassa.ConnectionPool(keyspace, server_list=[ip])
    def insert(self, cf_str, key, values):
        """insert(key, columns[, timestamp][, ttl][, write_consistency_level])
        cf: ColumnFamily String"""
        cf = self.get_cf(cf_str)
        if cf is None:
            return
        
        cf.insert(key, values)
        
    def get_range(self, cf_str):
        """get_range([start][, finish][, columns][, column_start][, column_finish]
        [, column_reversed][, column_count][, row_count][, include_timestamp]
        [, super_column][, read_consistency_level][, buffer_size][, filter_empty])"""
        rs = None
        
        cf = self.get_cf(cf_str)
        if not cf is None:
            try:
                rs = cf.get_range()
            except pycassa.cassandra.c10.ttypes.NotFoundException:
                pass
            
        return rs
        
    def get(self, cf_str, key, super_column, column_start, column_finish, column_count = 20000):
        """get(key[, columns][, column_start][, column_finish][, column_count]
        [, column_reversed][, include_timestamp][, super_column][, read_consistency_level])
        """
        rs = None
        cf = self.get_cf(cf_str)
        if cf is None:
            return rs
        
        try:
            rs = cf.get(key=key, super_column=super_column, column_start=column_start, column_finish=column_finish, column_count=column_count)
        except pycassa.cassandra.c10.ttypes.NotFoundException:
            pass
            
        return rs
    
    def getbykey(self, cf_str, key):
        """get(key[, columns][, column_start][, column_finish][, column_count]
        [, column_reversed][, include_timestamp][, super_column][, read_consistency_level])
        """
        rs = None
        cf = self.get_cf(cf_str)
        if cf is None:
            return rs
        
        try:
            rs = cf.get(key=key)
        except pycassa.cassandra.c10.ttypes.NotFoundException:
            pass
            
        return rs
        
    def getbykey2(self, cf_str, key, super_column, column_count):
        """get(key[, columns][, column_start][, column_finish][, column_count]
        [, column_reversed][, include_timestamp][, super_column][, read_consistency_level])
        """
        rs = None
        cf = self.get_cf(cf_str)
        if not cf is None:
            try:
                rs = cf.get(key=key, super_column=super_column, column_count=column_count)
            except pycassa.cassandra.c10.ttypes.NotFoundException:
                pass
            
        return rs
        
    ########### private #########################################
    def get_cf(self, cf_str):
        """[private]"""
        if not self.cfs.has_key(cf_str):
            try:
                self.cfs[cf_str] = pycassa.ColumnFamily(self.db, cf_str)
            except pycassa.cassandra.c10.ttypes.NotFoundException:
                return None
        return self.cfs[cf_str]

