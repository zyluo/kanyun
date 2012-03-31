import sys
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
    print "Sending request ", param
    socket.send (json.dumps(param))

    #  Get the reply.
    message = socket.recv()
    print "Received reply ", "[", message, "]"
    
    return json.loads(message)
    
def main():
#    if len(sys.argv) <> 2:
#        logging.debug( "usage: python %s [1-3]" % sys.argv[0]
#        sys.exit(0)

#    worker_id = sys.argv[1]
#    if worker_id not in ['1', '2', '3']:
#        logging.debug( "usage: python %s [1-3]" % sys.argv[0]
#        sys.exit(0)
    if len(sys.argv) == 2:
        print "usage:\ntest_api_client\ntest_api_client <id> <cf> <scf>"
        return
        
    config = ConfigParser.ConfigParser()
    config.read("demux.conf")
    cfg = dict(config.items('Client'))
        
    context = zmq.Context()

    #  Socket to talk to server
    print "Connecting to hello world server..."
    api_client = context.socket(zmq.REQ)
    api_client.connect("tcp://%(api_host)s:%(api_port)s" % cfg)
    
    if len(sys.argv) == 4:
        row_id, cf_str, scf_str = sys.argv[1], sys.argv[2], sys.argv[3]
        param = [u'G', row_id, cf_str, scf_str]
        r = invoke(api_client, param)
        return


    #  Do 10 requests, waiting each time for a response
    for request in range (1,2):
        # cmd, row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to
        param = param_tmpl
        
        param[4] = 0
        param[5] = 2
        r = invoke(api_client, param)
        print 'SUM=', '(no result)' if r is None else r.values()[0]
        
        param[4] = 1
        r = invoke(api_client, param)
        print 'MAX=', '(no result)' if r is None else r.values()[0]
        
        param[4] = 2
        r = invoke(api_client, param)
        print 'MIX=', '(no result)' if r is None else r.values()[0]
        
        param[4] = 3
        r = invoke(api_client, param)
        print 'AVERAGE=', '(no result)' if r is None else r.values()[0]
    
    
if __name__ == '__main__':
    main()
