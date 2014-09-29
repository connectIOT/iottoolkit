'''
Created on Sept 26, 2014

An agent listens on a socket and discovers the capsule type from the output of Barista

The Agent sets the resource value of 11101/0/5900 Capsule Type Resource to the current type

@author: mjkoster
'''

if __name__ == '__main__' :
    
    import httplib
    import websocket
    import json
    from urlparse import urlparse
    import base64
    
    httpServer = 'http://barista.cloudapp.net:8080'
    #httpServer = 'http://192.168.1.200:8080'
    httpPathBase = '/domain/endpoints'
    basePath = httpServer + httpPathBase
    username = 'admin'
    password = 'secret'
    auth = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    ep_names = []
 
    def discoverEndpoints(basePath):
        uriObject = urlparse(basePath)
        httpConnection = httplib.HTTPConnection(uriObject.netloc)
        httpConnection.request('GET', uriObject.path, headers= \
                           {"Accept" : "application/json", "Authorization": ("Basic %s" % auth) })
        response = httpConnection.getresponse()
        print response.status, response.reason
        if response.status == 200:
            endpoints = json.loads(response.read())
        httpConnection.close()
        
        for endpoint in endpoints:
            if endpoint['type'] == 'LED-STRIP':
                ep_names.append(endpoint['name'])
        return ep_names
               

    def actuateLEDs(ep_names,color):
        for ep in ep_names:
            path = basePath + '/' + ep + '/11100/0/5900?noResp=true'
            print "PUT: " + color + '  to: ' + path
            uriObject = urlparse(path)
            httpConnection = httplib.HTTPConnection(uriObject.netloc)
            httpConnection.request('PUT',   uriObject.path + '?' + uriObject.query, color, \
                                     {"Content-Type" : "application/json", "Authorization": ("Basic %s" % auth)})
            response = httpConnection.getresponse()
            print response.status, response.reason
            httpConnection.close()

    
    def capsule2color(capsuleType):
        colorTable = {
        'kazaar':'00005000',
        'dharkan':'00404000',
        'ristretto':'18181000',
        'arpeggio':'20003000',
        'roma':'30302000',
        'livanto':'40100000',
        'capriccio':'00300000',
        'volluto':'50300000',
        'decaffeinato_intenso':'30001800',
        'vivalto_lungo':'20204000'              
        }
        return colorTable[capsuleType]

    
    def processPayload(payload):
        payload = json.loads(payload)
        if payload.has_key('currentCapsule'):
            print payload['currentCapsule']
            actuateLEDs(ep_names, capsule2color(payload['currentCapsule']))
                        
    """
    Start
    """
    print "Started"
    #system = SystemInstance(exampleConstructor)

    ep_names = discoverEndpoints(basePath)
           
    ws = websocket.WebSocket()
    ws.connect('ws://localhost:4001/ws')
    #ws.connect('ws://barista.cloudapp.net:4001/ws')
    print 'ws connected'
    try:
        while 1:
            processPayload(ws.recv())
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'
    ws.close()
    print 'closed'
    
    