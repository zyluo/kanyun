# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 Sina Corporation
# All Rights Reserved.
# Author: YuWei Peng <pengyuwei@gmail.com> 2012-3-23
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

import time
import json
import traceback
from kanyun.database.cassadb import CassaDb

"""
parse the agent data and save to db
"""

"""
# previous data in memory
# data format: {key: (value, D-value, instance_id, cf_str, scf_str)}
# example: {'/instance_0001#host/cpu/total/1': (92345, 12, 'instance_0001#host', 'cpu', 'total')}
"""
previous_data = dict()

cf_dict = {"nic": ('nic_incoming', 'nic_outgoing'), \
            "mem": ("mem_max","mem_free"), \
            "blk": ("blk_read","blk_write")
            }
            
            
def get_cf_str(cf_str):
    """
    [('cpu', 'total', (utc_time, cpu_usage)), 
    ('mem', 'total', (utc_time, max, free)), 
    ('nic', 'vnet8', (utc_time, incoming, outgoing())), 
    ('blk', 'vda', (utc_time, read, write)), 
    ('blk', 'vdb', (utc_time, read, write))],
    """
    if cf_dict.has_key(cf_str):
        return cf_dict[cf_str]
    else:
        return (cf_str, None)


def get_change(prekey, new_value):
    """
    # prekey: /instance_0001#host/cpu/total/
    # data: ["cpu", "total", [1332465360.033008, 9043400000000]]
    # data: ["mem", "total", [1332465360.033008, 3860180, 131072]]
    # return: the change. if key is cpu, the val2 is None
    """
    global previous_data
    val1 = 0
    val2 = None
    if previous_data.has_key(prekey):
        o = previous_data[prekey]
        val1 = new_value - o[0]
        #print '\t1:%s --> %s (%d)' % (o[0], new_value[1], val1)
    else:
        val1 = new_value
        #print '\t1:%s' % (val1)
                
    return val1
    

def parse_single(db, raw_cf_str, instance_id, value, keypath, scf_str):
    """value=[1332465360.033008, 9043400000000]"""
    cf_str, _ = get_cf_str(raw_cf_str)

    # get change
    prekey = keypath + '/' + cf_str + '/' + scf_str
    if cf_str in ['cpu']:
        val1 = value[1] # cpu_usage
        print "\tID=%s cpu usage=\033[1;32m%.02f%%\033[0m" \
               % (instance_id, float(val1))
    else:
        val1 = get_change(prekey, value[1])
    
    previous_data[prekey + '/1'] = (value[1], val1, instance_id, cf_str, scf_str)
    db.insert(cf_str, instance_id, {scf_str: {int(value[0]): str(val1)}})
    #print '\tbuf %s saved:key=%s, cf=%s' % (prekey + '/1', instance_id, cf_str)
    return [
        (cf_str, instance_id, {scf_str: {int(value[0]): str(val1)}})
        ]


def parse_multi(db, raw_cf_str, instance_id, value, keypath, scf_str):
    """value=[1332465360.033008, 9043400000000]"""
    cf_str1, cf_str2 = get_cf_str(raw_cf_str)
    val1 = 0
    val2 = 0

    # get change
    prekey1 = keypath + '/' + cf_str1 + '/' + scf_str
    prekey2 = keypath + '/' + cf_str2 + '/' + scf_str
    if raw_cf_str in ['mem']:
        val1 = value[1] # max
        val2 = value[2] # free
#        print "\tID=%s useable mem \033[1;32m%d/%d\033[0m" \
#                % (instance_id, int(val2), int(val1))
    else:
        val1 = get_change(prekey1, value[1]) # nic_incoming / blk_read
        val2 = get_change(prekey2, value[2]) # nic_outgoing / blk_write
        previous_data[prekey1] = (value[1], val1, instance_id, cf_str1, scf_str)
        previous_data[prekey2] = (value[2], val2, instance_id, cf_str2, scf_str)
    db.insert(cf_str1, instance_id, {scf_str: {int(value[0]): str(val1)}})
    db.insert(cf_str2, instance_id, {scf_str: {int(value[0]): str(val2)}})
    print '\t%s=\033[1;32m%s\033[0m saved\n\t%s=\033[1;32m%s\033[0m saved' \
            % (prekey1, str(val1), prekey2, str(val2))
    #print '\tkey=%s, cf=%s/%s 2 records saved' % (instance_id, cf_str1, cf_str2)
    return [
            (cf_str1, instance_id, {scf_str: {int(value[0]): str(val1)}})
            , (cf_str2, instance_id, {scf_str: {int(value[0]): str(val2)}})
            ]

def get_uuid(tool, nova_id):
    # 1.open nova.mysql
    # 2.get id from instance_id
    # 3.select uuid from instances where id=id
    # 4. return uuid
    instance_uuid = tool.get_uuid_by_novaid(nova_id)
    
    return instance_uuid
    
def plugin_decoder_agent(tool, db, data):
    """decoder the agent data, and save into cassandra database.
    # db: cassandra ConnectionPool
    # data example: 
        {"instance-00000001@pyw.novalocal": 
            [
                ["cpu", "total", [1332465360.033008, 9043400000000]], 
                ["mem", "total", [1332465360.033008, 131072, 131072]], 
                ["nic", "vnet0", [1332465360.038922, 3860180, 1025563]], 
                ["blk", "vda", [1332465360.044262, 474624, 4741120]], 
                ["blk", "vdb", [1332465360.046606, 122880, 0]]
            ]
        }
    """
    global cfs
    global previous_data
    
    if len(data) <= 0:
        print 'invalid data:', data
        
        return False
        
    if db is None:
        return False
    
    pass_time = time.time()
    pre_data = None
    val1 = 0
    val2 = 0
    for nova_id, data in data.iteritems():
        # TODO:translate instance_id to instance_uuid
#        instance_id = nova_id
        instance_id = get_uuid(tool, nova_id)
        print nova_id, "-->", instance_id
        
        keypath = '/' # use for previous_data's key
        keypath += instance_id

        for i in data:
            # i is ["cpu", "total", [1332465360.033008, 9043400000000]], 
            scf_str = i[1]

            value = i[2]
            if i[0] in ['cpu']:
                parse_single(db, i[0], instance_id, value, keypath, scf_str)
            elif i[0] in ['mem', 'nic', 'blk']:
                parse_multi(db, i[0], instance_id, value, keypath, scf_str)
            else:
                print 'Not support type:', i[0]
                return False

    print '\t%d buffer, spend \033[1;33m%f\033[0m seconds' % (len(previous_data), time.time() - pass_time)
    print '-' * 60
    return True
    
    
if __name__ == '__main__':
    test_str = """
    {"instance-00000001@pyw.novalocal": 
    [
        ["cpu", "total", [1332465360.033008, 9043400000000]], 
        ["mem", "total", [1332465360.033008, 131072, 131072]], 
        ["nic", "vnet0", [1332465360.038922, 3860180, 1025563]], 
        ["blk", "vda", [1332465360.044262, 474624, 4741120]], 
        ["blk", "vdb", [1332465360.046606, 122880, 0]]
    ]
}
    """
    test_data = json.loads(test_str)
    plugin_decoder_agent(None, test_data)
