# encoding: utf-8
# TAB char: space
#
# Author: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-23
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-3-23

import time
import json
import traceback
from kanyun.database.cassadb import CassaDb

"""
db struce:
+-------------------------------------+
| cf=cpu/mem/...(one item one cf )    |
+-------------------------------------+---------+
| scf=total/devname                             |
+==============+==============+=======+=========+
|              | col=utc_time | time2 | ...     |
+==============+==============+=======+=========+
| key=instance | val1(subval) | val2  | ...     |
+===============================================+

db data format:
cf = pycassa.ColumnFamily(db, 'cpu')
cf.insert('instance', {u'total': {1332389700: 11}})
cf.insert('instance', {u'blk': {1332389700: (22, 33)}})

data format:
{"instance@hostname": 
    [
        ('cpu', 'total', (utc_time, cpu_time)), 
        ('mem', 'total', (utc_time, max, free)), 
        ('nic', 'vnet8', (utc_time, incoming, outgoing(内网))), 
        ('blk', 'vda', (utc_time, read, write)), 
        ('blk', 'vdb', (utc_time, read, write))
    ]
}
example:
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

"""
# ColumnFamilys object collection
# data format: {key: ColumnFamily Object}
# example: {'cpu', ColumnFamily()}
"""
#cfs = dict()

"""
# previous data in memory
# data format: {key: (value, D-value, instance_id, cf_str, scf_str)}
# example: {'/instance_0001#host/cpu/total/1': (92345, 12, 'instance_0001#host', 'cpu', 'total')}
"""
previous_data = dict()

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
        val1 = new_value[1] - o[0]
        print '\t1:%s --> %s (%d)' % (o[0], new_value[1], val1)
    else:
        val1 = new_value[1]
        print '\t1:%s' % (val1)
                
    return val1
    
cf_dict = {"nic": ('nic_incoming', 'nic_outgoing'), \
            "mem": ("mem_max","mem_free"), \
            "blk": ("blk_read","blk_write")
            }
def get_cf_str(cf_str):
    """
    [('cpu', 'total', (utc_time, cpu_usage)), 
    ('mem', 'total', (utc_time, max, free)), 
    ('nic', 'vnet8', (utc_time, incoming, outgoing(内网))), 
    ('blk', 'vda', (utc_time, read, write)), 
    ('blk', 'vdb', (utc_time, read, write))],
    """
    if cf_dict.has_key(cf_str):
        return cf_dict[cf_str]
    else:
        return (cf_str, None)

#def get_cf(db, cf_str):
#    """cf_str is get_cf_str(str)
#    return cf/None"""
#    cf = None
#    if cfs.has_key(cf_str):
#        cf = cfs[cf_str]
#    else:
#        print 'create cf connection:', cf_str
#        try:
#            cfs[cf_str] = pycassa.ColumnFamily(db, cf_str)
#            cf = cfs[cf_str]
#        except pycassa.cassandra.c10.ttypes.NotFoundException:
#            print cf_str, "NotFound"
#        
#    return cf

def parse_single(db, raw_cf_str, instance_id, value, keypath, scf_str):
    """value=[1332465360.033008, 9043400000000]"""
    cf_str, _ = get_cf_str(raw_cf_str)
#    cf = get_cf(db, cf_str)
#    if cf is None:
#        print "Unsupport cf type:", cf_str
#        return
    # get change
    prekey = keypath + '/' + cf_str + '/' + scf_str
    if cf_str in ['cpu']:
        val1 = value[1]
    else:
        val1 = get_change(prekey, value)
    
    previous_data[prekey + '/1'] = (value[1], val1, instance_id, cf_str, scf_str)
#    cf.insert(instance_id, {scf_str: {int(value[0]): str(val1)}})
    db.insert(cf_str, instance_id, {scf_str: {int(value[0]): str(val1)}})
    print '\tbuf %s saved:key=%s, cf=%s' % (prekey + '/1', instance_id, cf_str)

def parse_multi(db, raw_cf_str, instance_id, value, keypath, scf_str):
    """value=[1332465360.033008, 9043400000000]"""
#    cf2 = None
    cf_str1, cf_str2 = get_cf_str(raw_cf_str)
#    cf1 = get_cf(db, cf_str1)
#    if cf1 is None:
#        print "unsupport cf type:", cf_str1
#        return
#    cf2 = get_cf(db, cf_str2)
#    if cf2 is None:
#        print "unsupport cf type :", cf_str2
#        return
    # get change
    prekey1 = keypath + '/' + cf_str1 + '/' + scf_str
    prekey2 = keypath + '/' + cf_str2 + '/' + scf_str
    if raw_cf_str in ['mem']:
        val1 = value[1]
        val2 = value[2]
    else:
        val1 = get_change(prekey1, value)
        val2 = get_change(prekey2, value)
        previous_data[prekey1] = (value[1], val1, instance_id, cf_str1, scf_str)
        previous_data[prekey2] = (value[2], val2, instance_id, cf_str2, scf_str)
#        cf1.insert(instance_id, {scf_str: {int(value[0]): str(val1)}})
#        cf2.insert(instance_id, {scf_str: {int(value[0]): str(val2)}})
        db.insert(cf_str1, instance_id, {scf_str: {int(value[0]): str(val1)}})
        db.insert(cf_str2, instance_id, {scf_str: {int(value[0]): str(val2)}})
        print '\t%s saved\n\t%s saved' % (prekey1, prekey2)
        print '\tkey=%s, cf=%s/%s 2 records saved' % (instance_id, cf_str1, cf_str2)

def plugin_decoder_agent(db, data):
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
        return
        
    if db is None:
        return
    
    pass_time = time.time()
    pre_data = None
    val1 = 0
    val2 = 0
    for instance_id, data in data.iteritems():
        keypath = '/' # use for previous_data's key
        keypath += instance_id
#        print '***** instance=%s:%d ColumnFamilys *****' % (instance_id, len(cfs))

        for i in data:
            # i is ["cpu", "total", [1332465360.033008, 9043400000000]], 
            scf_str = i[1]
#            cf2 = None
#            cf_str1, cf_str2 = get_cf_str(i[0])
#            cf1 = get_cf(db, cf_str1)
#            if cf1 is None:
#                return

            value = i[2]
            if i[0] in ['cpu']:
                parse_single(db, i[0], instance_id, value, keypath, scf_str)
            elif i[0] in ['mem', 'nic', 'blk']:
#                cf2 = get_cf(cf_str2)
#                if cf2 is None or len(i[2]) < 2:
#                    return
                parse_multi(db, i[0], instance_id, value, keypath, scf_str)
            else:
                print 'Not support type:', i[0]
                return
#            # get change
#            prekey = keypath + '/' + cf_str1 + '/' + scf_str
#            if i[1] in ['cpu', 'mem', 'blk']:
#                val1 = value[1]
#                val2 = value[2]
#            else:
#                val1, val2 = get_change(prekey, i)
#            
#            if val2 is None:
#                previous_data[prekey + '/1'] = (value[1], val1, instance_id, cf_str1, scf_str)
#                cf1.insert(instance_id, {scf_str: {int(value[0]): str(val1)}})
#                print '\t%s=%d(%s) saved' % (prekey, val1, str(val1))
#                print '\tkey=%s, cf=%s saved' % (instance_id, cf_str1)
#            else:
#                previous_data[prekey + '/1'] = (value[1], val1, instance_id, cf_str1, scf_str)
#                previous_data[prekey + '/2'] = (value[2], val2, instance_id, cf_str2, scf_str)
#                cf1.insert(instance_id, {scf_str: {int(value[0]): str(val1)}})
#                if not cf2 is None:
#                    cf2.insert(instance_id, {scf_str: {int(value[0]): str(val2)}})
#                print '\t%s saved\n\t%s saved' % (prekey + '/1', prekey + '/2')
#                print '\tkey=%s, cf=%s 2 records saved' % (instance_id, cf_str1)

    print '\t%d buffer, spend \033[1;33m%f\033[0m seconds' % (len(previous_data), time.time() - pass_time)
    print '-' * 60
    
    
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
