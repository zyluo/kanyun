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

import time
import json
import logging
import traceback
from collections import OrderedDict

class HallBuffer():
    """
    example:
        k = hit_test([p1, p2]):
        if k not None:
            bufdata = getbuf(k)
            return bufdata
        # // not hit, do your work,
        # such as select * from data and save into data;
        # ... 
        cleanup() # optional
        save(k, data)
    """
    def __init__(self):
        # buf format: key:[bufdata, hit_times, last_hit_Time, create_time]
        self.buf = dict()

    def save(self, key, data):
        if isinstance(key, list):
            key = str(key)
        now = time.time()
        self.buf[key] = [data, 0, now, now]
        return data
        
    def cleanup(self, time_out = 300, max_count = 999):
        count = 0
        new = dict()
        for key, i in self.buf.iteritems():
            count += 1
            print i
            if count > max_count:
                break;
            if (time.time() - i[3] < time_out):
                print "\t", time.time(),"-", i[3],"<",time_out
                new[key] = i
        self.buf = new
        
    def hit_test(self, key):
        if isinstance(key, list):
            key = str(key)    
        if self.buf.has_key(key):
            self.buf[key][1] += 1
            self.buf[key][2] = time.time()
            return True
        else:
            return False

    def get_buf(self, key):
        if isinstance(key, list):
            key = str(key)
        if self.buf.has_key(key):
            return self.buf[key][0];
        else:
            return None
            
    def get_hit_rate(self, key):
        if isinstance(key, list):
            key = str(key)
        if self.buf.has_key(key):
            return self.buf[key][1]
        else:
            return 0
        
if __name__ == '__main__':
    params = ["iPhone", 2012]
    data = "detail of 2012 iPhone 4S"
    params2 = ["iPad", 2013]
    data2 = "detail of 2012 iPad"
    
    b = HallBuffer()
    key = str(params)
    print "Hit rate=", b.get_hit_rate(key), "of", len(b.buf)
    
    if b.hit_test(key):
        print b.get_buf(key)
        assert False
    else:
        b.save(key, data)
        time.sleep(3)
        b.save(str(params2), data2)
        print "not hit."
    print "Hit rate=", b.get_hit_rate(key), "of", len(b.buf)
        
    if b.hit_test(key):
        print "hit!"
        print "\t", b.get_buf(key)
    else:
        b.save(key, data)
        assert False
    print "Hit rate=", b.get_hit_rate(key), "of", len(b.buf)
    
    assert len(b.buf) == 2
    
    b.cleanup(time_out = 1)
    print "after cleanup, Hit rate=", b.get_hit_rate(key), "of", len(b.buf)
    assert len(b.buf) == 1
