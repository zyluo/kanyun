import ConfigParser
import json
import zmq

"""
protocol:
[CMD, row_id, cf_str, scf_str, statistic, period, time_from, time_to]
example:
[u'S', u'instance-00000001@pyw.novalocal', u'cpu', u'total', 0, 5, 1332897600, 0]
"""

def call(socket, param):
    print "Sending request ", param
    socket.send (json.dumps(param))

    #  Get the reply.
    message = socket.recv()
    print "Received reply ", "[", message, "]"
    
    return json.loads(message)
    
def main():
    config = ConfigParser.ConfigParser()
    config.read("demux.conf")
    server_cfg = dict(config.items('Demux'))
        
    context = zmq.Context()

    #  Socket to talk to server
    print "Connecting to hello world server..."
    api_client = context.socket(zmq.REQ)
    api_client.connect("tcp://localhost:%(api_port)s" % server_cfg)

    #  Do 10 requests, waiting each time for a response
    for request in range (1,2):
        # cmd, row_id, cf_str, scf_str, statistic, period=period, time_from=time_from, time_to=time_to
        param = ['S', 'instance-00000001@pyw.novalocal', 'cpu', 'total', 0, 5, 1332897600, 0]
        
        param[4] = 0
        param[5] = 2
        r = call(api_client, param)
        print 'SUM=', r.values()[0]
        
        param[4] = 1
        r = call(api_client, param)
        print 'MAX=', r.values()[0]
        
        param[4] = 2
        r = call(api_client, param)
        print 'MIX=', r.values()[0]
        
        param[4] = 3
        r = call(api_client, param)
        print 'AVERAGE=', r.values()[0]
    
    
if __name__ == '__main__':
    main()
