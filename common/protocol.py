#!/usr/bin/env python

"""
msg_type = 'lb'
msg_id = str(uuid.uuid1())

======== client -> server ==============

# 'create_lb'
msg_body = {'cmd': 'create_lb',
            'msg': {'user_name': 'myUser',
                    'tenant': 'myTenant',
                    'load_balancer_id': 'myLB',
                    # http, tcp
                    'protocol': http,
                    'listen_port': 80,
                    'instance_port': 80,
                    # round_robin, source_binding
                    'balancing_method': 'round_robin',
                    'health_check_timeout_ms': 5,
                    'health_check_interval_ms': 0.5,
                    # if http
                    'health_check_target_path': '/',
                    'health_check_fail_count': 2,
                    # elif tcp
                    'health_check_healthy_treshold':10,
                    'health_check_unhealthy_treshold':2,
                    # end if
                    'instance_uuids': ["a-uuid", "b-uuid", "c-uuid"],
                    'http_server_names': ['www.abc.com', 'www.xyz.com'],
                   }
           }

# 'delete_lb' or 'read_lb'
message = {'cmd': 'delete_lb',
           'msg': {'user_name': 'myUser',
                   'tenant': 'myTenant',
                   'load_balancer_id': 'myLB',
                  }
          }

# 'read_lb_list'
message = {'cmd': 'read_lb_list',
           'msg': {'user_name': 'myUser'
                   'tenant': 'myTenant'
                  }
          }

# After you create a load balancer, you can modify any of the settings,
# except for Load Balancer Name and Port Configuration.

# To rename a load balancer or change its port configuration,
# create a replacement load balancer.

# 'update_lb_config'
message = {'cmd': 'update_lb_config',   
           'msg': {'user_name': 'myUser',
                   'tenant': 'myTenant',
                   'load_balancer_id': 'myLB',
                   # round_robin, source_binding
                   'balancing_method': 'round_robin',
                   'health_check_timeout_ms': 5,
                   'health_check_interval_ms': 0.5,
                   # if http
                   'health_check_target_path': '/',
                   'health_check_fail_count': 2,
                   # elif tcp
                   'health_check_healthy_treshold':10,
                   'health_check_unhealthy_treshold':2,
                  }
          }

# 'update_lb_instances'
message = {'cmd': 'update_lb_instances',   
           'msg': {'user_name': 12,
                   'tenant': 'myTenant',
                   'load_balancer_id': 'myLB',
                   'instance_uuids': ["a-uuid", "b-uuid", "c-uuid"],
                  }
          }

# 'update_lb_http_server_names'
message = {'cmd': 'update_lb_http_server_names',
           'msg': {'user_name': 12,
                   'tenant': 'myTenant',
                   'load_balancer_id': 'myLB',
                   'http_server_names': ['www.abc.com', 'www.xyz.com'],
                  }
          }

======== server -> client ==============

# 'create_lb', 'update_lb', 'delete_lb'
to_client = {'cmd': <cmd>,
             'msg' {'desc': 'message string'
                    # 200 or 500
                    'code': 200,
                   }
            }

# 'read_lb'
to_client = {'cmd': <cmd>,
             'msg': {'user_name': 'myUser',
                     'tenant': 'myTenant',
                     'load_balancer_id': 'myLB',
                     # round_robin, source_binding
                     'balancing_method': 'round_robin',
                     'health_check_timeout_ms': 5,
                     'health_check_interval_ms': 0.5,
                     # if http
                     'health_check_target_path': '/',
                     'health_check_fail_count': 2,
                     # elif tcp
                     'health_check_healthy_treshold':10,
                     'health_check_unhealthy_treshold':2,
                     # end if
                     'instance_uuids': ["a-uuid", "b-uuid", "c-uuid"],
                     'http_server_names': ['www.abc.com', 'www.xyz.com'],
                    }
            }

# 'read_lb_list'
to_client = {'cmd': <cmd>,
             'msg': {'user_name': 'myUser',
                     'tenant': 'myTenant',
                     'load_balancer_list': [{'load_balancer_id': 'myLB',
                                             # http, tcp
                                             'protocol': http,
                                             'listen_port': 80,
                                             'instance_port': 80,
                                            },
                                            {'load_balancer_id': 'myLB',
                                             # http, tcp
                                             'protocol': http,
                                             'listen_port': 80,
                                             'instance_port': 80,
                                            },
                                           ],
                    }
            }

======== server -> worker ==============

# 'create_lb', 'update_lb' -> all data of lb must be sent to worker
to_worker = {'cmd': 'create_lb',
             'msg': {'user_name': 'myUser',
                     'tenant': 'myTenant',
                     'load_balancer_id': 'myLB',
                     # http, tcp
                     'protocol': 'http',
                     'listen_port': 80,
                     'instance_port': 80,
                     # round_robin, source_binding
                     'balancing_method': 'round_robin',
                     'health_check_timeout_ms': 5,
                     'health_check_interval_ms': 0.5,
                     # if http
                     'health_check_target_path': '/',
                     'health_check_fail_count': 2,
                     # elif tcp
                     'health_check_healthy_treshold':10,
                     'health_check_unhealthy_treshold':2,
                     # end if
                     'instance_uuids': ["a-uuid", "b-uuid", "c-uuid"],
                     # add instance fixed ips and send to worker
                     'instance_ips': ['10.4.5.6', '10.3.4.5', '10.8.8.8']
                     'http_server_names': ['www.abc.com', 'www.xyz.com'],
                    }
            }

# 'delete_lb'
to_worker= {'cmd': 'delete_lb',
            'msg': {'user_name': 'myUser'
                    'tenant': 'myTenant'
                    'load_balancer_id': 'myLB',
                   }
           }

======== worker -> server ==============

from_worker = {'cmd': <cmd>,
               'msg' {'worker_id': 2,
                      # 200 or 500
                      'code': 200,
                      'desc': 'message string'
                     }
              }
"""
