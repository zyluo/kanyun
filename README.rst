Overview
===========================

The kanyun is a monitoring system of openstack.
kanyun是一个openstack的监控系统。它可以监控虚拟机的CPU使用率、内存使用、网络流量和磁盘读写情况。
kanyun包括worker、data-server、API-server三个模块。
worker模块负责采集监控数据并交由data-server进行存储，APIserver则提供进行查询和统计的外部接口。

kanyun采集的数据可以由dashboard进行展示，或者由计费系统（如dough）计费使用。

拓扑
----

总览::

                    +-----------------+
                    |    cassandra    |
                    +-----------------+
                      |            |
                      |            |
                +-----------+ +-------------+
                |   server  | |  API-server |   <---- statisticer
                +-----------+ +-------------+
                       | 
                       |    
                     woker
                       |   
               ________|___________        
             /         |           \
     外网流量采集   虚拟机信息采集  其他采集模块 

Server::


                         +--- <-- Worker's PUSH
                         |
                         |
                    +----------+
                    |   PULL   |     <-- feedback
                +---|==========|
    Client--->  |REP|  Server  |
                +---|==========|
                    |   PUB    |     <-- broadcast
                    +----------+
                         |
                         |
                         +----> Worker's SUB
                         +----> DB

部署::

安装cassandra数据库
创建和配置/etc/kanyun.conf
在服务器上启动kanyun-api和kanyun-server
在nova-compute节点上启动kanyun-worker

通讯协议
------

数据通讯全部使用json格式


外网流量采集模块--->worker
------------------------

格式::

    {'instanceid1':('IP', time, 'value'), 'instanceid2':('IP', time, 'value')}
    value的单位：KB


示例::

    {'instance-00000001': ('10.0.0.2', 1332409327, '0')}

虚拟机信息采集模块-->worker


格式::

    [('cpu', 'total', (utc_time, cpu_usage)), 
    ('mem', 'total', (utc_time, max, free)), 
    ('nic', 'vnet8', (utc_time, incoming, outgoing(内网))), 
    ('blk', 'vda', (utc_time, read, write)), 
    ('blk', 'vdb', (utc_time, read, write))],

示例::

    {'instance-000000ba@sws-yz-5': 
    [('cpu', 'total', (1332400088.149444, 5)),  
    ('mem', 'total', (1332400088.149444, 8388608L, 8388608L)), 
    ('nic', 'vnet8', (1332400088.152285, 427360746L, 174445810L)), 
    ('blk', 'vda', (1332400088.156346, 298522624L, 5908590592L)), 
    ('blk', 'vdb', (1332400088.158202, 2159616L, 1481297920L))], 
    其中cpu和mem为实际使用量

worker-->server
----------------

格式::

    ['msg_type', data]

    'msg_type'取值：
        HEART_BEAT = '0'
        LOCAL_INFO = '1'
        TRAFFIC_ACCOUNTING = '2'
        AGENT = '3'

示例

心跳::
    ['WORKER1', time.time(), status]
    status：0为即将正常退出，服务器收到0就会取消对该worker的状态监控；1为正在工作中
    数据：
    ['2', 
        ''{"instance-00000001@pyw.novalocal": 
            [
             ["cpu", "total", [1332831360.029795, 53522870000000]], 
             ["mem", "total", [1332831360.029795, 131072, 131072]], 
             ["nic", "vnet0", [1332831360.037399, 21795245, 5775663]], 
             ["blk", "vda", [1332831360.04699, 474624, 4851712]], 
             ["blk", "vdb", [1332831360.049333, 122880, 0]]
            ]
         }''
    ]

server-->cassandra
--------------------

格式::

    instance_id, {scf_str: {时间: 值}}

示例::

    Columnfamily为mem_max保存最大内存值，mem_free保存空闲内存值
    instance_id, {'total': {1332831360: 131072}}
    instance_id, {'total': {1332831360: 131072}}

billing -->API server
--------------------

格式::

    ['msg_type', 'uuid', {
        'method': 'query_usage_report',
        'args':  {
                'id': 'instance00001'
                'metric': 'network',
                'metric_param': 'vnet0',
                'statistic': 'sum',
                'period': 5,
                'timestamp_from': '2012-02-20T12:12:12',
                'timestamp_to': '2012-02-22T12:12:12',
            }
        }
    ]
    metric取值：

    'vmnetwork'
    'cpu'
    'mem_max'
    'mem_free'
    'nic_read'
    'nic_write'
    'blk_read'
    'blk_write'
    metric_param取值：

    如果metric为vmnetwork或者cpu或者mem*的话，为'total'
    其他情况为设备名，比如'vnet0'、'vda'等
    statistic取值:

    'sum'
    'max'
    'min'
    'avg'
    'sam'(暂时不支持)

示例

协议请求数据示例::

    ['msg_type', 'uuid', {
        'method': 'query_usage_report',
        'args':  {
                'id': 'instance00001'
                'metric': 'vmnetwork',
                'metric_param': 'vnet0',
                'statistic': 'sum',
                'period': 5,
                'timestamp_from': '2012-02-20T12:12:12',
                'timestamp_to': '2012-02-22T12:12:12',
            }
        }
    ]
api_client示例::

    api-client instance-00000001@pyw.novalocal cpu total sum 5 2012-02-20T12:12:12 2012-06-20T12:12:12

    获取存在指定数据的全部实例列表： 
    api_client vmnetwork 
    获取指定实例的数据： 
    api_client -k instance-0000002 
    获取指定类型、指定实例、指定参数的数据： 
    api_client instance-0000002 vmnetwork 10.0.0.2 api_client instance-00000012@lx12 cpu api_client instance-00000012@lx12 mem mem_free 
    查询指定实例、指定类型、指定参数、指定统计类型的数据，以5分钟为统计单位、从指定时间开始到当前时间进行统计，返回统计结果： 
    api_client instance-0000002 vmnetwork 10.0.0.2 0 5 1332897600 0


API server--> billing
--------------------

格式::

    ['msg_type', 'uuid',
        {'code': 0,
         'message': 'success',
         'data':{key:result},
        }
    ]

示例::

    [ {"1332897600.0": 10} ]

数据库


结构::

    +--------------+
    | cf=vmnetwork |
    +--------------+-------------------------------------------+
    | scf=IP                                                   |
    +===================+===========+=======+==================+
    |                   | col=time1 | time2 | ...              |
    +===================+===========+=======+==================+
    | key=instance_id   |   val1    | val2  | ...              |
    +==========================================================+

    +---------------------------------------------------------------------------------------------+
    | cf=cpu/mem_max/mem_free/nic_read/nic_write/blk_read/blk_write/...(one item as one cf )      |
    +---------------------------------------------------------------------------------------------+
    | scf=total/devname(vnet0/vda...)                  |
    +=================+==============+=======+=========+
    |                 | col=utc_time | time2 | ...     |
    +=================+==============+=======+=========+
    | key=instance_id | val1(subval) | val2  | ...     |
    +==================================================+

建库
----

可以在数据库本地使用cassandra-cli -h 127.0.0.1连接数据库并执行以下命令建库::

    CREATE keyspace DATA;
    USE DATA;
     
    CREATE COLUMN family vmnetwork WITH column_type='Super' AND comparator='AsciiType' AND subcomparator='IntegerType' AND default_validation_class='AsciiType';
    CREATE COLUMN family cpu WITH column_type='Super' AND comparator='AsciiType' AND subcomparator='IntegerType' AND default_validation_class='AsciiType';
    CREATE COLUMN family mem_max WITH column_type='Super' AND comparator='AsciiType' AND subcomparator='IntegerType' AND default_validation_class='AsciiType';
    CREATE COLUMN family mem_free WITH column_type='Super' AND comparator='AsciiType' AND subcomparator='IntegerType' AND default_validation_class='AsciiType';
    CREATE COLUMN family nic_incoming WITH column_type='Super' AND comparator='AsciiType' AND subcomparator='IntegerType' AND default_validation_class='AsciiType';
    CREATE COLUMN family nic_outgoing WITH column_type='Super' AND comparator='AsciiType' AND subcomparator='IntegerType' AND default_validation_class='AsciiType';
    CREATE COLUMN family blk_read WITH column_type='Super' AND comparator='AsciiType' AND subcomparator='IntegerType' AND default_validation_class='AsciiType';
    CREATE COLUMN family blk_write WITH column_type='Super' AND comparator='AsciiType' AND subcomparator='IntegerType' AND default_validation_class='AsciiType';
     
    assume vmnetwork KEYS AS ascii;
    assume cpu KEYS AS ascii;
    assume mem_max KEYS AS ascii;
    assume nic_incoming KEYS AS ascii;
    assume nic_outgoing KEYS AS ascii;
    assume blk_read KEYS AS ascii;
    assume blk_write KEYS AS ascii;
    assume mem_free KEYS AS ascii;

schema::

    [DEFAULT@DATA] SHOW schema;
    CREATE keyspace DATA
      WITH placement_strategy = 'NetworkTopologyStrategy'
      AND strategy_options = {datacenter1 : 1}
      AND durable_writes = true;
     
    USE DATA;
     
    CREATE COLUMN family blk_read
      WITH column_type = 'Super'
      AND comparator = 'AsciiType'
      AND subcomparator = 'IntegerType'
      AND default_validation_class = 'AsciiType'
      AND key_validation_class = 'BytesType'
      AND rows_cached = 0.0
      AND row_cache_save_period = 0
      AND row_cache_keys_to_save = 2147483647
      AND keys_cached = 200000.0
      AND key_cache_save_period = 14400
      AND read_repair_chance = 1.0
      AND gc_grace = 864000
      AND min_compaction_threshold = 4
      AND max_compaction_threshold = 32
      AND replicate_on_write = true
      AND row_cache_provider = 'SerializingCacheProvider'
      AND compaction_strategy = 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy';
     
    CREATE COLUMN family blk_write
      WITH column_type = 'Super'
      AND comparator = 'AsciiType'
      AND subcomparator = 'IntegerType'
      AND default_validation_class = 'AsciiType'
      AND key_validation_class = 'BytesType'
      AND rows_cached = 0.0
      AND row_cache_save_period = 0
      AND row_cache_keys_to_save = 2147483647
      AND keys_cached = 200000.0
      AND key_cache_save_period = 14400
      AND read_repair_chance = 1.0
      AND gc_grace = 864000
      AND min_compaction_threshold = 4
      AND max_compaction_threshold = 32
      AND replicate_on_write = true
      AND row_cache_provider = 'SerializingCacheProvider'
      AND compaction_strategy = 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy';
     
    CREATE COLUMN family cpu
      WITH column_type = 'Super'
      AND comparator = 'AsciiType'
      AND subcomparator = 'IntegerType'
      AND default_validation_class = 'AsciiType'
      AND key_validation_class = 'BytesType'
      AND rows_cached = 0.0
      AND row_cache_save_period = 0
      AND row_cache_keys_to_save = 2147483647
      AND keys_cached = 200000.0
      AND key_cache_save_period = 14400
      AND read_repair_chance = 1.0
      AND gc_grace = 864000
      AND min_compaction_threshold = 4
      AND max_compaction_threshold = 32
      AND replicate_on_write = true
      AND row_cache_provider = 'SerializingCacheProvider'
      AND compaction_strategy = 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy';
     
    CREATE COLUMN family mem_free
      WITH column_type = 'Super'
      AND comparator = 'AsciiType'
      AND subcomparator = 'IntegerType'
      AND default_validation_class = 'AsciiType'
      AND key_validation_class = 'BytesType'
      AND rows_cached = 0.0
      AND row_cache_save_period = 0
      AND row_cache_keys_to_save = 2147483647
      AND keys_cached = 200000.0
      AND key_cache_save_period = 14400
      AND read_repair_chance = 1.0
      AND gc_grace = 864000
      AND min_compaction_threshold = 4
      AND max_compaction_threshold = 32
      AND replicate_on_write = true
      AND row_cache_provider = 'SerializingCacheProvider'
      AND compaction_strategy = 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy';
     
    CREATE COLUMN family mem_max
      WITH column_type = 'Super'
      AND comparator = 'AsciiType'
      AND subcomparator = 'IntegerType'
      AND default_validation_class = 'AsciiType'
      AND key_validation_class = 'BytesType'
      AND rows_cached = 0.0
      AND row_cache_save_period = 0
      AND row_cache_keys_to_save = 2147483647
      AND keys_cached = 200000.0
      AND key_cache_save_period = 14400
      AND read_repair_chance = 1.0
      AND gc_grace = 864000
      AND min_compaction_threshold = 4
      AND max_compaction_threshold = 32
      AND replicate_on_write = true
      AND row_cache_provider = 'SerializingCacheProvider'
      AND compaction_strategy = 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy';
     
    CREATE COLUMN family nic_incoming
      WITH column_type = 'Super'
      AND comparator = 'AsciiType'
      AND subcomparator = 'IntegerType'
      AND default_validation_class = 'AsciiType'
      AND key_validation_class = 'BytesType'
      AND rows_cached = 0.0
      AND row_cache_save_period = 0
      AND row_cache_keys_to_save = 2147483647
      AND keys_cached = 200000.0
      AND key_cache_save_period = 14400
      AND read_repair_chance = 1.0
      AND gc_grace = 864000
      AND min_compaction_threshold = 4
      AND max_compaction_threshold = 32
      AND replicate_on_write = true
      AND row_cache_provider = 'SerializingCacheProvider'
      AND compaction_strategy = 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy';
     
    CREATE COLUMN family nic_outgoing
      WITH column_type = 'Super'
      AND comparator = 'AsciiType'
      AND subcomparator = 'IntegerType'
      AND default_validation_class = 'AsciiType'
      AND key_validation_class = 'BytesType'
      AND rows_cached = 0.0
      AND row_cache_save_period = 0
      AND row_cache_keys_to_save = 2147483647
      AND keys_cached = 200000.0
      AND key_cache_save_period = 14400
      AND read_repair_chance = 1.0
      AND gc_grace = 864000
      AND min_compaction_threshold = 4
      AND max_compaction_threshold = 32
      AND replicate_on_write = true
      AND row_cache_provider = 'SerializingCacheProvider'
      AND compaction_strategy = 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy';
     
    CREATE COLUMN family nic_read
      WITH column_type = 'Super'
      AND comparator = 'AsciiType'
      AND subcomparator = 'IntegerType'
      AND default_validation_class = 'AsciiType'
      AND key_validation_class = 'BytesType'
      AND rows_cached = 0.0
      AND row_cache_save_period = 0
      AND row_cache_keys_to_save = 2147483647
      AND keys_cached = 200000.0
      AND key_cache_save_period = 14400
      AND read_repair_chance = 1.0
      AND gc_grace = 864000
      AND min_compaction_threshold = 4
      AND max_compaction_threshold = 32
      AND replicate_on_write = true
      AND row_cache_provider = 'SerializingCacheProvider'
      AND compaction_strategy = 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy';
     
    CREATE COLUMN family nic_write
      WITH column_type = 'Super'
      AND comparator = 'AsciiType'
      AND subcomparator = 'IntegerType'
      AND default_validation_class = 'AsciiType'
      AND key_validation_class = 'BytesType'
      AND rows_cached = 0.0
      AND row_cache_save_period = 0
      AND row_cache_keys_to_save = 2147483647
      AND keys_cached = 200000.0
      AND key_cache_save_period = 14400
      AND read_repair_chance = 1.0
      AND gc_grace = 864000
      AND min_compaction_threshold = 4
      AND max_compaction_threshold = 32
      AND replicate_on_write = true
      AND row_cache_provider = 'SerializingCacheProvider'
      AND compaction_strategy = 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy';
     
    CREATE COLUMN family vmnetwork
      WITH column_type = 'Super'
      AND comparator = 'AsciiType'
      AND subcomparator = 'IntegerType'
      AND default_validation_class = 'AsciiType'
      AND key_validation_class = 'BytesType'
      AND rows_cached = 0.0
      AND row_cache_save_period = 0
      AND row_cache_keys_to_save = 2147483647
      AND keys_cached = 200000.0
      AND key_cache_save_period = 14400
      AND read_repair_chance = 1.0
      AND gc_grace = 864000
      AND min_compaction_threshold = 4
      AND max_compaction_threshold = 32
      AND replicate_on_write = true
      AND row_cache_provider = 'SerializingCacheProvider'
      AND compaction_strategy = 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy';

配置文件样例::

    bin/kanyun.conf
    [log]
    file=/tmp/kanyun.log
     
    [server]
    host: *
    port: 5551
    db_host: 127.0.0.1
     
    [api]
    api_host: *
    api_port: 5556
    db_host: 127.0.0.1
     
    [worker]
    id: worker1
    worker_timeout: 60
    dataserver_host: 127.0.0.1
    dataserver_port: 5551
    log: /tmp/kanyun-worker.log
     
    [client]
    api_host: 127.0.0.1
    api_port: 5556
