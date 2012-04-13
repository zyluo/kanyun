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

import pycassa

class CassaDb():

    def __init__(self, keyspace = 'data', ip = '127.0.0.1'):
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
        if cf is None or key is None or values is None:
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
        if cf is None or key is None or super_column is None or column_start is None or column_finish is None:
            return rs
        
        try:
            rs = cf.get(key=key, super_column=super_column, column_start=column_start, column_finish=column_finish, column_count=column_count)
        except pycassa.cassandra.c10.ttypes.NotFoundException:
            pass
        except pycassa.cassandra.c10.ttypes.InvalidRequestException:
            print 'cassandra db InvalidRequest.'
            pass
            
        return rs
    
    def getbykey(self, cf_str, key):
        """get(key[, columns][, column_start][, column_finish][, column_count]
        [, column_reversed][, include_timestamp][, super_column][, read_consistency_level])
        """
        rs = None
        cf = self.get_cf(cf_str)
        if cf is None or key is None:
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
        if cf is None or key is None or super_column is None or column_count is None:
            return None
            
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

