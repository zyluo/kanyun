#!/usr/bin/env python

import ConfigParser
import threading

import MySQLdb
import MySQLdb.cursors

rlock = threading.RLock()

conn = None

cu = None

def get_conn():
    global conn
    global cu
    try:
        conn.ping()
    except Exception:
        config = ConfigParser.ConfigParser()
        config.read("demux.conf")
        conn = MySQLdb.connect(cursorclass=MySQLdb.cursors.DictCursor,
                               **dict(config.items('MySQL')))
        cu = conn.cursor()

get_conn()

select_listen_port = ("SELECT deleted, listen_port FROM load_balancer "
                      "WHERE listen_port >= 11000;")

select_http_server_names = ("SELECT id FROM http_server_name "
                            "WHERE deleted is FALSE;")

select_lb_ids = ("SELECT id as load_balancer_id FROM load_balancer "
                 "WHERE deleted is FALSE;")

select_lb_cfg = ("SELECT deleted, user_id as user_name, project_id as tenant, "
                        "id as load_balancer_id, protocol, "
                        "listen_port, instance_port, balancing_method, "
                        "health_check_timeout_ms, health_check_interval_ms, "
                        "health_check_target_path, "
                        "health_check_healthy_threshold, "
                        "health_check_unhealthy_threshold "
                 "FROM load_balancer lb "
                 "WHERE user_id=%(user_name)s "
                         "AND project_id=%(tenant)s "
                         "AND id=%(load_balancer_id)s;")

select_lb_list = ("SELECT id as load_balancer_id, protocol, "
                         "listen_port, instance_port, balancing_method, "
                         "health_check_timeout_ms, health_check_interval_ms, "
                         "health_check_target_path, "
                         "health_check_healthy_threshold, "
                         "health_check_unhealthy_threshold "
                  "FROM load_balancer "
                  "WHERE deleted is FALSE "
                        "AND user_id=%(user_name)s "
                        "AND project_id=%(tenant)s;")

delete_lb_config = ("UPDATE load_balancer SET deleted=True "
                    "WHERE id=%(load_balancer_id)s;")

delete_instances = ("UPDATE load_balancer_instance_association "
                    "SET deleted=True "
                    "WHERE load_balancer_id=%(load_balancer_id)s;")

delete_http_server_names = ("UPDATE http_server_name SET deleted=True "
                            "WHERE load_balancer_id=%(load_balancer_id)s;")

select_fixed_ips = ("SELECT j.address FROM instances i, fixed_ips j "
                    "WHERE i.deleted is FALSE "
                            "AND i.id=j.instance_id "
                            "AND i.uuid=%s;")

select_lb_http_server_names = ("SELECT id FROM http_server_name "
                               "WHERE deleted is FALSE "
                                   "AND load_balancer_id=%(load_balancer_id)s")

select_lb_instance_uuids = ("SELECT i.uuid FROM instances i,"
                                    "load_balancer_instance_association a "
                            "WHERE i.deleted is FALSE "
                                    "AND a.deleted is FALSE "
                                    "AND i.id=a.instance_id "
                                    "AND a.load_balancer_id="
                                        "%(load_balancer_id)s;")

select_instance_by_uuid = ("SELECT id AS instance_id "
                           "FROM instances "
                           "WHERE deleted=FALSE "
                                   "AND uuid=%(instance_uuid)s;")

_create_lb_cfg = ("INSERT INTO load_balancer "
                              "(deleted, id, user_id, project_id, protocol, "
                              "listen_port, instance_port, balancing_method, "
                              "health_check_timeout_ms, "
                              "health_check_interval_ms, "
                              "health_check_target_path, "
                              "health_check_healthy_threshold, "
                              "health_check_unhealthy_threshold) "
                  "VALUES (FALSE, %(load_balancer_id)s, %(user_name)s, "
                                "%(tenant)s, %(protocol)s, "
                                "%(listen_port)s, %(instance_port)s, "
                                "%(balancing_method)s, "
                                "%(health_check_timeout_ms)s, "
                                "%(health_check_interval_ms)s, "
                                "%(health_check_target_path)s, "
                                "%(health_check_healthy_threshold)s, "
                                "%(health_check_unhealthy_threshold)s);")

_update_lb_cfg = ("UPDATE load_balancer "
                  "SET deleted=False, user_id=%(user_name)s, "
                      "project_id=%(tenant)s, protocol=%(protocol)s, "
                      "listen_port=%(listen_port)s, "
                      "instance_port=%(instance_port)s, "
                      "balancing_method=%(balancing_method)s, "
                      "health_check_timeout_ms=%(health_check_timeout_ms)s, "
                      "health_check_interval_ms=%(health_check_interval_ms)s, "
                      "health_check_target_path=%(health_check_target_path)s, "
                      "health_check_healthy_threshold="
                              "%(health_check_healthy_threshold)s, "
                      "health_check_unhealthy_threshold="
                              "%(health_check_unhealthy_threshold)s "
                  "WHERE id=%(load_balancer_id)s;")

_update_lb_instance = ("INSERT INTO load_balancer_instance_association "
                              "(deleted, load_balancer_id, instance_id) "
                       "VALUES (FALSE, %(load_balancer_id)s, %(instance_id)s) "
                       "ON DUPLICATE KEY UPDATE "
                               "deleted=FALSE;")

_update_lb_http_server_name = ("INSERT INTO http_server_name "
                                       "(deleted, id, load_balancer_id) "
                               "VALUES (FALSE, %(http_server_name)s, "
                                       "%(load_balancer_id)s) "
                               "ON DUPLICATE KEY UPDATE "
                                       "deleted=FALSE;")

def _read_lb_cfg(*args, **kwargs):
    cnt = cu.execute(select_lb_cfg, kwargs)
    return cu.fetchone() or dict()

def _select_lb_http_server_names(*args, **kwargs):
    cnt = cu.execute(select_lb_http_server_names, kwargs)
    http_server_names = cu.fetchall()
    return map(lambda x: x['id'], http_server_names)

def create_lb(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        'protocol',
        'instance_port',
        'balancing_method',
        'health_check_timeout_ms',
        'health_check_interval_ms',
        'health_check_target_path',
        'health_check_healthy_threshold',
        'health_check_unhealthy_threshold',
        'instance_uuids',
        'http_server_names'
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    lb_cfg = _read_lb_cfg(*args, **kwargs)
    if not lb_cfg.get('deleted', True):
        raise Exception('Load balancer name already exists')
    elif kwargs['balancing_method'] not in ["round_robin", "source_binding"]:
        raise Exception("Invalid balancing method")
    elif not 1 <= kwargs['instance_port'] <= 65535:
        raise Exception("Instance port out of range")
    with rlock:
        protocol = kwargs['protocol']
        if protocol == "tcp":
            listen_port = allocate_listen_port()
            if listen_port > 65535:
                raise Exception("Max listen port exceeded")
            elif not 1 <= kwargs['health_check_healthy_threshold'] <= 10:
                raise Exception("Healthy threshold out of range")
            elif not 1 <= kwargs['health_check_unhealthy_threshold'] <= 10:
                raise Exception("Unhealthy threshold out of range")
            kwargs['listen_port'] = listen_port
        elif protocol == "http":
            http_server_names = filter(lambda x: x,
                                       map(lambda y: y.strip(),
                                           kwargs.get('http_server_names',
                                                      [])))
            all_server_names = _read_http_server_name_all()
            dup_server_names = filter(lambda x: x in all_server_names,
                                      http_server_names)
            if not http_server_names:
                raise Exception('HTTP server name absent')
            elif dup_server_names:
                raise Exception('%s server name already exists' %
                                dup_server_names[0])
            kwargs['http_server_names'] = http_server_names
            kwargs['listen_port'] = 80
        else:
            raise Exception("Invalid protocol")
        if lb_cfg:
            cnt = cu.execute(_update_lb_cfg, kwargs)
        else:
            cnt = cu.execute(_create_lb_cfg, kwargs)
        conn.commit()
    if protocol == "http":
        update_lb_http_server_names(*args, **kwargs)
    update_lb_instances(*args, **kwargs)

def read_lb(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    lb_cfg = _read_lb_cfg(*args, **kwargs)
    if lb_cfg.get('deleted', True):
        raise Exception('Load balancer does not exists')
    cnt = cu.execute(select_lb_instance_uuids, kwargs)
    uuids = cu.fetchall()
    lb_cfg['instance_uuids'] = map(lambda x: x['uuid'], uuids)
    if lb_cfg['protocol'] == 'http':
        lb_cfg['http_server_names'] = _select_lb_http_server_names(*args,
                                                                   **kwargs)
    else:
        lb_cfg['http_server_names'] = []
    return lb_cfg

def read_lb_list(*args, **kwargs):
    get_conn()
    exp_keys = [
        'user_name',
        'tenant',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    cnt = cu.execute(select_lb_list, kwargs)
    lb_list = cu.fetchall()
    for lb_dict in lb_list:
        cnt = cu.execute(select_lb_instance_uuids, lb_dict)
        uuids = cu.fetchall()
        lb_dict['instance_uuids'] = map(lambda x: x['uuid'], uuids)
        if lb_dict['protocol'] == 'http':
            lb_dict['http_server_names'] = _select_lb_http_server_names(*args,
                                                                    **lb_dict)
        else:
            lb_dict['http_server_names'] = []
    return {"load_balancer_list": lb_list,
            "user_name": kwargs.get("user_name"),
            "tenant": kwargs.get("tenant")}

def update_lb_config(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        'protocol',
        'balancing_method',
        'health_check_timeout_ms',
        'health_check_interval_ms',
        'health_check_target_path',
        'health_check_healthy_threshold',
        'health_check_unhealthy_threshold',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    if kwargs.get('protocol') == 'http':
        kwargs['health_check_healthy_threshold'] = 0
        kwargs['health_check_unhealthy_threshold'] = 0
        kwargs['health_check_target_path'] = kwargs.get(
                                             'health_check_target_path',
                                             '/')
    elif kwargs.get('protocol') == 'tcp':
        kwargs['health_check_target_path'] = ""
        if not 1 <= kwargs['health_check_healthy_threshold'] <= 10:
            raise Exception("Healthy threshold out of range")
        elif not 1 <= kwargs['health_check_unhealthy_threshold'] <= 10:
            raise Exception("Unhealthy threshold out of range")
    else:
        raise Exception("Invalid protocol")
    lb_cfg = _read_lb_cfg(*args, **kwargs)
    if lb_cfg.get('deleted', True):
        raise Exception('Load balancer does not exists')
    lb_cfg.update(kwargs)
    cnt = cu.execute(_update_lb_cfg, lb_cfg)
    conn.commit()

def update_lb_instances(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        'protocol',
        'instance_uuids',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    cnt = cu.execute(delete_instances, kwargs)
    conn.commit()
    uuids = kwargs.get('instance_uuids', [])
    for uuid in uuids:
        cnt = cu.execute(select_instance_by_uuid, {'instance_uuid': uuid})
        asdf = cu.fetchone().get("instance_id")
        if asdf is not None:
            cnt = cu.execute(_update_lb_instance,
                             {'instance_id': asdf,
                              'load_balancer_id': kwargs['load_balancer_id']})
    conn.commit()


def update_lb_http_server_names(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        'protocol',
        'http_server_names',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    protocol = kwargs['protocol']
    if protocol != "http":
        return
    lb_server_names = _select_lb_http_server_names(*args, **kwargs)
    all_server_names = _read_http_server_name_all()
    dup_server_names = filter(lambda x: x not in lb_server_names and
                                        x in all_server_names,
                              kwargs.get('http_server_names', []))
    if dup_server_names:
        raise Exception('%s server name already exists' % dup_server_names[0])
    cnt = cu.execute(delete_http_server_names, kwargs)
    conn.commit()
    https = kwargs.get('http_server_names', [])
    for h in https:
        cnt = cu.execute(_update_lb_http_server_name,
                         {'http_server_name': h,
                          'load_balancer_id': kwargs['load_balancer_id']})
    conn.commit()

def delete_lb(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    cnt = cu.execute(delete_lb_config, kwargs)
    cnt = cu.execute(delete_instances, kwargs)
    cnt = cu.execute(delete_http_server_names, kwargs)
    conn.commit()

def read_whole_lb(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        'load_balancer_id',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    lb_info = _read_lb_cfg(*args, **kwargs)
    cnt = cu.execute(select_lb_instance_uuids, kwargs)
    uuids = map(lambda x: x['uuid'], cu.fetchall())
    instance_ips = list()
    for uuid in uuids:
        cnt = cu.execute(select_fixed_ips, uuid)
        ips = cu.fetchall()
        instance_ips.extend(map(lambda x: x['address'], ips))
    lb_info['instance_ips'] = instance_ips
    lb_info['instance_uuids'] = uuids
    if lb_info['protocol'] == 'http':
        lb_info['http_server_names'] = _select_lb_http_server_names(*args,
                                                                   **kwargs)
    else:
        lb_info['http_server_names'] = []
    return lb_info

def allocate_listen_port():
    cnt = cu.execute(select_listen_port)
    res = cu.fetchall()
    used_ports = map(lambda x: x['listen_port'],
                     filter(lambda y: not y['deleted'], res))
    available_ports = filter(lambda x: x not in used_ports,
                             map(lambda y: y['listen_port'],
                                 filter(lambda z: z['deleted'], res)))
    if available_ports:
        return available_ports[0]
    elif used_ports:
        return max(used_ports) + 1
    else:
        return 11000

def read_load_balancer_id_all(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    cnt = cu.execute(select_lb_ids)
    return {"load_balancer_ids": map(lambda x: x['load_balancer_id'],
                                     cu.fetchall())}

def _read_http_server_name_all():
    cnt = cu.execute(select_http_server_names)
    return map(lambda x: x['id'], cu.fetchall())

def read_http_server_name_all(*args, **kwargs):
    exp_keys = [
        'user_name',
        'tenant',
        ]
    assert(all(map(lambda x: x in kwargs.keys(), exp_keys)))

    return {"http_server_names": _read_http_server_name_all()}
