import subprocess
import shlex
import time

"""
A worker plugin run in nova-network node, get the network traffic.
Protocol format:
{'10.0.0.2': {'11111': '12'}, '10.0.0.3': {'11122': '45'}}
cf.insert('10.0.0.2', {u'usage': {1332389700: '12'}})

request:
sudo iptables -t raw -I PREROUTING -s 10.0.0.3 -j RETURN
sudo iptables -t raw -I PREROUTING -s 10.0.0.2 -j RETURN

db:
+--------------+
| cf=vmnetwork |
+--------------+-------------------------------------------+
| scf=IP                                                   |
+===================+===========+=======+==================+
|                   | col=time1 | time2 | ...              |
+===================+===========+=======+==================+
| key=instance_name |   val1    | val2  | ...              |
+==========================================================+
"""

CMD = "sudo iptables -t raw -nvxL PREROUTING"

ip_bytes = {} # {'10.0.0.2': '10', '10.0.0.3': '5'}

def get_traffic_accounting_info():
    """
    return value format:
    {'10.0.0.2': (11111, '12'), '10.0.0.3': (11112, '16')}
    """
    records = subprocess.check_output(shlex.split(CMD), stderr=subprocess.STDOUT)
    lines = records.splitlines()[2:]
    ret = {}
   
    for line in lines:
        counter_info = line.split()
        out_bytes = counter_info[1]
        instance_ip = counter_info[7]
        val = int(out_bytes)

        if instance_ip in ip_bytes:
            val_str = ip_bytes[instance_ip]
            val = int(out_bytes) - int(val_str)
            if val < 0:
                val = int(out_bytes)
        else:
            ip_bytes[instance_ip] = str(out_bytes)
            
        ret[instance_ip] = (int(time.time()), str(val));

    return ret

if __name__=='__main__':
    print get_traffic_accounting_info()
