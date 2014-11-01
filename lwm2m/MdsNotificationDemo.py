'''
Created on October 25th, 2014

Subscribe to a resource, connect to the notification channel of an mDS instance and receive 
notifications from the subscribed resource

Process the notifications and filter a set of endpoints and a particular resource path. Index the 
resource value from the notification and use it to actuate an indicator.

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
    subscribeURI = '/3302/0/5500'
    #actuateURI = '/11101/0/5901'
    actuateURI = '/11100/0/5900' # use the chainable LED or LED strip
    baseURL = httpServer + resourcePathBase
    
    username = 'connected-home'
    password = 'secret'
    auth = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    ep_names = []
 
    def discoverEndpoints(basePath):
        uriObject = urlparse(basePath)
        print 'discoverEP : ' + basePath
        httpConnection = httplib.HTTPConnection(uriObject.netloc)
        httpConnection.request('GET', uriObject.path, headers= \
                           {"Accept" : "application/json", "Authorization": ("Basic %s" % auth) })
        response = httpConnection.getresponse()
        print response.status, response.reason
        if response.status == 200:
            endpoints = json.loads(response.read())
        httpConnection.close()
        
        for endpoint in endpoints:
            if endpoint['type'] == 'DEMO' and discoverResources(endpoint['name'], subscribeURI):
                ep_names.append(endpoint['name'])
                print 'endpoint: ' + endpoint['name']
        return ep_names

    def discoverResources(endpoint, uri_path):
        resources = []
        uriObject = urlparse(baseURL + '/' + endpoint)
        print 'discoverRES : ' + endpoint
        httpConnection = httplib.HTTPConnection(uriObject.netloc)
        httpConnection.request('GET', uriObject.path, headers= \
                           {"Accept" : "application/json", "Authorization": ("Basic %s" % auth) })
        response = httpConnection.getresponse()
        print response.status, response.reason
        if response.status == 200:
            resources = json.loads(response.read())
        httpConnection.close()
        
        for resource in resources:
            if resource['uri'] == uri_path:
                print 'resource: ' + resource['uri']
                return resource['uri']
            else:
                return 0

    def subscribe(resourceURI):
        for ep in ep_names:
            path = httpServer + '/' + httpDomain + '/subscriptions' + '/' + ep + subscribeURI + '?sync=true'
            print "subscribe: " + path
            uriObject = urlparse(path)
            httpConnection = httplib.HTTPConnection(uriObject.netloc)
            httpConnection.request('PUT',   uriObject.path + '?' + uriObject.query, "", \
                                     {"Content-Type" : "application/json", "Authorization": ("Basic %s" % auth)})
            response = httpConnection.getresponse()
            print response.status, response.reason
            httpConnection.close()

    def longPoll(channelPath):
        print 'poll: ' + channelPath
        uriObject = urlparse(channelPath)
        httpConnection = httplib.HTTPConnection(uriObject.netloc)
        while 1:
            httpConnection.request('GET', uriObject.path, headers= \
                           {"Accept" : "application/json", "Authorization": ("Basic %s" % auth) })
            response = httpConnection.getresponse()
            print response.status, response.reason
            if response.status == 200:
                httpBody = response.read()
                if len(httpBody) > 0:
                    handleNotifications(json.loads(httpBody))

    def handleNotifications(events):
        if 'notifications' in events:
            for notification in events['notifications']:
                if (notification['ep'] in ep_names) and (notification['path'] == subscribeURI):
                    process_payload(notification)
                
    def process_payload(notification):
        value =  base64.b64decode(notification['payload']) #notification payloads are base64 encoded
        print "value: ", value
        """
        ledString = ""
        for led in range(10):
            if float(value)/10 > led:
                ledString += '1'
            else:
                ledString += '0'
        actuateLED(ledString)
        """
        if value == '1':
            actuateLED('FF000000')
        else:
            actuateLED('00000000')
        
    def actuateLED(ledString = ''):
        for ep in ep_names:
            path = baseURL + '/' + ep + actuateURI
            print "actuating: " + path + ", value=" + ledString
            uriObject = urlparse(path)
            httpConnection = httplib.HTTPConnection(uriObject.netloc)
            httpConnection.request('PUT',   uriObject.path + '?' + uriObject.query, ledString, \
                               {"Content-Type" : "application/json", "Authorization": ("Basic %s" % auth)})
            response = httpConnection.getresponse()
            print response.status, response.reason
            httpConnection.close()    
                
    """
    Start
    """
    print "Started"

    discoverEndpoints(baseURL)
    
    subscribe(subscribeURI)
    
    try:
        longPoll(httpServer + '/' + httpDomain + '/notification/pull')
        
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'
    print 'closed'
    
    