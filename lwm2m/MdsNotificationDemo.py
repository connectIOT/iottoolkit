'''
Created on October 25th, 2014

Subscribe to a resource and connect to the notification channel of an mDS instance and receive 
notifications from the subscribed resource

@author: mjkoster
'''

if __name__ == '__main__' :
    
    import httplib
    import json
    from urlparse import urlparse
    import base64
    
    httpServer = 'http://barista2.cloudapp.net:8080'
    httpPathBase = '/domain/endpoints'
    resourceURI = '3302/0/5500'
    baseURL = httpServer + httpPathBase
    resourceURL = baseURL + resourceURI
    
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
            if endpoint['type'] == 'presenceDemo':
                ep_names.append(endpoint['name'])
        return ep_names
               

    def actuateLEDs(color):
        for ep in ep_names:
            path = baseURL + '/' + ep + '/11100/0/5900?sync=false'
            print "PUT: " + color + '  to: ' + path
            uriObject = urlparse(path)
            httpConnection = httplib.HTTPConnection(uriObject.netloc)
            httpConnection.request('PUT',   uriObject.path + '?' + uriObject.query, color, \
                                     {"Content-Type" : "application/json", "Authorization": ("Basic %s" % auth)})
            response = httpConnection.getresponse()
            print response.status, response.reason
            httpConnection.close()

 
    """
    Start
    """
    print "Started"

    discoverEndpoints(baseURL)
    
    try:
        while 1:
            pass                
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'
    print 'closed'
    
    