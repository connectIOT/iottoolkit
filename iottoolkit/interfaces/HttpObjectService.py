'''
Created on Oct 18, 2012

Create a RESTlite instance of a http server for SmartObjects. 
based on wsgi/restlite with the restObject extensions to match object path segments 
to resource names e.g. the URL path: /object1/barometricPressure/Description/Observers 
maps to the python API identifier: object1.barometricPressure.Description.Observers

@author: mjkoster
'''

import wsgiref
import urllib
import threading
from restlite import restlite
from restlite import restObject
from socket import gethostname, getfqdn


# Extend restObject classes with content handlers and provide a local bind method to pick up local extensions
class Request(restObject.Request):
    def __init__(self, env, start_response):
        self.env, self.start_response = env, start_response
        restObject.Request.__init__(self.env, self.start_response)
        

class RestObject(restObject.RestObject):
    def __init__(self, rootObject, users):
        restObject.RestObject.__init__(self, rootObject, users)
        
    def contentTypeNegotiate(self, accepts, providedTypes):
        accepts = accepts.split(',')
        prefs = []
        for accept in accepts:
            accept = accept.split(';')
            if len(accept) > 1:
                accept[1] = int( float( accept[1].strip('q=') ) * 10 ) # scale q values to 0..10
            else:
                accept.append(10) # no q value means 1.0, scaled to 1..10
            prefs.append(accept)
        prefs.sort(lambda self,(x,y) : y )
        for prefType in prefs : # try highest to lowest q values, header order if equal
            for contentType in providedTypes : # scan provided types for a match
                if contentType == prefType[0] :
                    return contentType
        if prefType[0] == '*/*' :
            return providedTypes[0] # return our favorite type if we don't have a preferred type and */* is allowed
        else:
            raise restlite.Status('415 Unsupported Media Type') # no applicable type and client doesn't want whatever
        
    def _handleGET(self, currentResource):
        # if it's a complex structure class, invoke the serializer
        
        if hasattr(currentResource,'serialize') : # see if the resource has a serialize method
            responseType = self.contentTypeNegotiate(self.env['HTTP_ACCEPT'], currentResource.serializeContentTypes() )
            self.start_response('200 OK', [('Content-Type', responseType)]) 
            return currentResource.serialize( currentResource.get(), responseType )
        else:
            return restObject.RestObject._handleGET(self, currentResource) # default GET does JSON and XML
    
    def _handlePUT(self, currentResource):
        if hasattr(currentResource, 'parse') :
            responseType = self.contentTypeNegotiate(self.env['HTTP_ACCEPT'], currentResource.parseContentTypes() )
            currentResource.set( currentResource.parse( self.request.getBody() , responseType ))
        else :
            restObject.RestObject._handlePUT(self, currentResource) # default PUT
    
    def _handlePOST(self, currentResource):
        if hasattr(currentResource, 'parse') :
            responseType = self.contentTypeNegotiate(self.env['HTTP_ACCEPT'], currentResource.parseContentTypes() )
            currentResource.create( currentResource.parse( self.request.getBody() , responseType ))
        else :
            restObject.RestObject._handlePOST(self, currentResource) # default POST
    
    def _handleDELETE(self, currentResource):
        if hasattr(currentResource, 'parse') :
            responseType = self.contentTypeNegotiate(self.env['HTTP_ACCEPT'], currentResource.parseContentTypes() )
            currentResource.delete( currentResource.parse( self.request.getBody() , responseType ))
        else :
            restObject.RestObject._handleDELETE(self, currentResource) # default DELETE


def bind(rootObject, users=None):
    '''The bind method to bind the returned wsgi application to the supplied data and users.
    @param data the original Python data structure which is used and updated as needed.
    @param users the optional users dictionary. If missing, it disables access control.
    @return:  the wsgi application that can be used with restlite.
    '''
    restObject = RestObject(rootObject, users)
    def handler(env, start_response):
        return restObject.handler(env, start_response)
    return handler


class HttpHandler(object):
    def __init__(self, baseObject): # get a handle to the Object Service root dictionary
        self.objectHandler = bind(baseObject, users=None) 
        #bind to root resource dictionary passed to constructor  
        #bind returns the RestObject handler which uses the Request object
        # the handler calls the overriding _handleXX methods in this module
        self.routes = [(r'GET /favicon.ico$', self.favicon_handler),(r'GET,PUT,POST,DELETE ', self.objectHandler )]
        return 
    
    def favicon_handler(self, env, start_response) :
        start_response('200 OK', [('Content-Type', 'image/gif')]) 
        try:
            with open('favicon.ico', 'rb') as f: result = f.read()
        except: raise restlite.Status, '400 Error Reading File'
        return(result)

                  
class HttpObjectService(object):   
    def __init__(self, baseObject=None, port=None): 

        if port == None:
            self._port=8000
        else:
            self._port = port  # default port 8000
            
        if baseObject == None:
            from SmartObject.SmartObject import SmartObject
            self._baseObject = SmartObject()
        else:
            self._baseObject = baseObject
            
        self.resources = self._baseObject.resources
        
        if port != None or baseObject == None:
            self.start()
    @property        
    def baseObject(self):
        return self._baseObject
    
    def start(self, port=None): 
        if port!=None:
            self._port=port # override port on start if supplied
        httpThread = threading.Thread(target = self._startHttpObjectService)
        httpThread.daemon = True
        httpThread.start()
        self._baseObject.Properties.update({'httpService': 'http://' + gethostname() + ':' + repr(self._port)})
       
    def _startHttpObjectService(self):
        from wsgiref.simple_server import make_server
        # HttpObjectService constructor method creates a Smart Object service and 
        # returns a constructor for a restlite router instance
        self.httpObjectHandler = HttpHandler(self._baseObject)
        self.httpd = make_server('', self._port, restlite.router(self.httpObjectHandler.routes))
        try: self.httpd.serve_forever()
        except KeyboardInterrupt: pass
