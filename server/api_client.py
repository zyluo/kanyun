#!/usr/bin/env python

import sys
import time
import ConfigParser
import json
import zmq

"""
protocol:
[CMD, row_id, cf_str, scf_str, statistic, period, time_from, time_to]
example:
[u'S', u'instance-00000001@pyw.novalocal', u'cpu', u'total', 0, 5, 1332897600, 0]
"""

param_tmpl = ['S', 'instance-00000001@pyw.novalocal', 'cpu', 'total', 0, 5, 1332897600, 0]

def invoke(socket, param):
#    print "Sending request ", param
    socket.send (json.dumps(param))

    #  Get the reply.
    message = socket.recv()
#    print "Received reply ", "[", message, "]"
    
    return json.loads(message)
    
def invoke_getbykey(socket, row_id, cf_str, scf_str):
    param = [u'G', row_id, cf_str, scf_str]
    r = invoke(socket, param)
    if r is None:
        r = dict()
    for k, i in r.iteritems():
        print "{%s:%s}" % (k, i)
    print "%d results of cf=%s,scf=%s,key=%s" % (len(r), cf_str, scf_str, row_id)
    return r

def invoke_getbyInstanceID(socket, row_id):
    cmd = list()
    cmd.append([u'G', row_id, "nic", "vnet01"])
    cmd.append([u'G', row_id, "blk", "blk1"])
    cmd.append([u'G', row_id, "cpu", "total"])
    cmd.append([u'G', row_id, "mem", "total1"])
    cmd.append([u'G', row_id, "mem", "total2"])
    
    cmd = list()
    cmd.append([u'K', row_id, "mem"])
    
    for i in cmd:
        cf_str = i[2]
#        scf_str = i[3]
        r = invoke(socket, i)
        if r is None:
            r = dict()
#        print r
        for k, i in r.iteritems():
            print "%s.%s %d results" % (cf_str, k, len(i))
#            timestr = time.strftime("%m-%d %H:%M:%S", time.localtime(float(k)))
#            print "%s %s=%s" % (timestr, cf_str, i)
#        print "%d results of cf=%s,scf=%s,key=%s" % (len(r), cf_str, scf_str, row_id)

    
def invoke_statistics(api_client, row_id, cf_str, scf_str, statistic, period=5, time_from=0, time_to=0):
    #param_tmpl = ['S', 'instance-00000001@pyw.novalocal', 'cpu', 'total', 0, 5, 1332897600, 0]
    #  Do 10 requests, waiting each time for a response
    for request in range (1,2):
        # cmd, row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to
        param = ['S', row_id, cf_str, scf_str, int(statistic), int(period), int(time_from), int(time_to)]
        
        timestr1 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(time_from)))
        if int(time_to) == 0:
            timestr2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        else:
            timestr2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(time_to)))
        print 'statistics info of %s(period=%s)' % (row_id, period)
        print 'time range:%s --> %s ' % (timestr1, timestr2)
        param[4] = 0
        param[5] = 2
        r = invoke(api_client, param)
        print 'SUM=', '(no result)' if r is None else r.values()[0]
        
        param[4] = 1
        r = invoke(api_client, param)
        print 'MAX=', '(no result)' if r is None else r.values()[0]
        
        param[4] = 2
        r = invoke(api_client, param)
        print 'MIN=', '(no result)' if r is None else r.values()[0]
        
        param[4] = 3
        r = invoke(api_client, param)
        print 'AVERAGE=', '(no result)' if r is None else r.values()[0]
    
def main():
#    if len(sys.argv) <> 2:
#        logging.debug( "usage: python %s [1-3]" % sys.argv[0]
#        sys.exit(0)

#    worker_id = sys.argv[1]
#    if worker_id not in ['1', '2', '3']:
#        logging.debug( "usage: python %s [1-3]" % sys.argv[0]
#        sys.exit(0)
    if len(sys.argv) == 2:
        if sys.argv[1] in ['--help', "-h", "?"]:
            print "usage:"
            print "\tapi_client <id>"
            print "\tapi_client\n\tapi_client <id> <cf> <scf>"
            print "\tapi_client <id> <cf> <scf> <statistic> <period> <time_from> [time_to]"
            print "example:"
            print "\tapi_client instance-0000002 vmnetwork 10.0.0.2"
            print "\tapi_client instance-0000002"
            print "\tapi_client instance-0000002 vmnetwork 10.0.0.2 statistic 5 1332897600 0"
            return
        
    config = ConfigParser.ConfigParser()
    config.read("demux.conf")
    cfg = dict(config.items('Client'))
        
    context = zmq.Context()

    #  Socket to talk to server
#    print "Connecting to hello world server..."
    api_client = context.socket(zmq.REQ)
    api_client.connect("tcp://%(api_host)s:%(api_port)s" % cfg)
    
    if len(sys.argv) == 4:
        invoke_getbykey(api_client, sys.argv[1], sys.argv[2], sys.argv[3])
        return
    elif len(sys.argv) == 2:
        invoke_getbyInstanceID(api_client, sys.argv[1])
        return
    elif len(sys.argv) == 8:
        invoke_statistics(api_client, sys.argv[1], sys.argv[2], sys.argv[3],sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
        return
    elif len(sys.argv) == 7:
        invoke_statistics(api_client, sys.argv[1], sys.argv[2], sys.argv[3],sys.argv[4], sys.argv[5], sys.argv[6], '0')
        return

    
if __name__ == '__main__':
    main()
