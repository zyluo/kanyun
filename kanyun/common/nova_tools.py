#!/usr/bin/env python
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

import sys
import time
import ConfigParser
import json
from collections import OrderedDict
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

from kanyun.common.app import *

class NovaTools():
    def __init__(self, app):
        self.app = app
        self.cfg = self.app.get_cfg("DEFAULT")
        self.db = create_engine(self.cfg["sql_connection"])
        self.db.echo = False
        metadata = MetaData(self.db)
        self.instances = Table('instances', metadata, autoload=True)
        
    def get_uuid_by_novaid(self, instance):
        ret = self.get_id(instance)
        if ret is None:
            return None
            
        ret = self.get_instances(id=ret)
        if ret is None:
            return None
            
        return ret[1]
        
    def get_id(self, instance):
        if len(instance) < 17:
            return None
            
        ret = None
        try:
            ret = int(instance[9:17], 16)
        except:
            ret = None
        return ret
        
    def get_instances(self, uuid=None, id=None):
        "return format: (id, uuid, display_name) or None"
        if not uuid is None:
            stmt = self.instances.select(self.instances.c.uuid == uuid)
        elif not id is None:
            stmt = self.instances.select(self.instances.c.id == id)
        else:
            return None
        rs = stmt.execute()
        if not rs is None:
            row = rs.first()
            if row is None:
                return None
            return (row[4], row[34], row[26])
        return None
        
if __name__ == '__main__':
    app = App(conf="/etc/nova/nova.conf", log='/tmp/kanyun.log')
    tool = NovaTools(app)
    rs = tool.get_instances(uuid='76d6f296-68b8-4a21-9a20-9f46ff48d6ef')
    print rs
    print tool.get_id("instance-00000138")
