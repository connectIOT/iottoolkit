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
    httpDomain = 'domain'
    resourcePathBase = '/' + httpDomain + '/endpoints'
    subscribeURI = '3302/0/5500'
    actuateURI = '11101/0/5901'
    baseURL = httpServer + resourcePathBase
    
    username = 'admin'
    password = 'secret'
    auth = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    ep_names = []
 
    def discoverEndpoints(basePath):
        uriObject = urlparse(basePath)
        print 'discover: ' + basePath
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
                print 'endpoint: ' + endpoint['name']
        return ep_names

    def subscribe(resourceURI):
        for ep in ep_names:
            path = httpServer + '/' + httpDomain + '/subscriptions' + '/' + ep + '/' + subscribeURI + '?sync=false'
            print "subscribe: " + path
            uriObject = urlparse(path)
            httpConnection = httplib.HTTPConnection(uriObject.netloc)
            httpConnection.request('PUT',   uriObject.path + '?' + uriObject.query, "", \
                                     {"Content-Type" : "application/json", "Authorization": ("Basic %s" % auth)})
            response = httpConnection.getresponse()
            print response.status, response.reason
            httpConnection.close()

    def poll(channelPath):
        uriObject = urlparse(channelPath)
        httpConnection = httplib.HTTPConnection(uriObject.netloc)
        httpConnection.request('GET', uriObject.path, headers= \
                           {"Accept" : "application/json", "Authorization": ("Basic %s" % auth) })
        response = httpConnection.getresponse()
        print response.status, response.reason
        if response.status == 200:
            return json.loads(response.read())
        print "Closing poll connection"
        httpConnection.close()

    def actuateLEDbar(ledString = '0000000000'):
        for ep in ep_names:
            path = baseURL + ep + actuateURI
            uriObject = urlparse(path)
            httpConnection = httplib.HTTPConnection(uriObject.netloc)
            httpConnection.request('PUT',   uriObject.path + '?' + uriObject.query, ledString, \
                               {"Content-Type" : "application/json", "Authorization": ("Basic %s" % auth)})
            response = httpConnection.getresponse()
            print response.status, response.reason
            httpConnection.close()    
    
    def process_notification(notification):
        value =  base64.b64decode(notification['payload']) #notification payloads are base64 encoded
        ledBarString = ""
        for led in range(10):
            if value/10 > led:
                ledBarString += '1'
            else:
                ledBarString += '0'
        actuateLEDbar(ledBarString)
                
    """
    Start
    """
    print "Started"

    discoverEndpoints(baseURL)
    subscribe(subscribeURI)
    
    try:
        while 1:
            domainEvents = poll(httpServer + '/' + httpDomain + 'notification/pull')
            print domainEvents
            if 'notifications' in domainEvents:
                for notification in domainEvents['notifications']:
                    if notification['ep'] in ep_names and notification['path'] == subscribeURI:
                        process_notification(notification)
            
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'
    print 'closed'
    
    