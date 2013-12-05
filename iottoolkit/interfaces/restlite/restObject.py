'''
restObject module

Based on the restdata module from restlite, the Request object sequences
the URL path by resource and authenticates at each level. The bind method walks 
the SmartObject directory structures according to the path segments
exposes methods for HTTP verbs that can be overridden in the service laver
(FIXME add semantic method based on structural triples?)
'''

import sys, json, base64, hashlib
import restlite

def hash(user, realm, password):
    '''MD5(user:realm:password) is used for storing user's encrypted password.'''
    return hashlib.md5('%s:%s:%s'%(user, realm, password)).hexdigest()

class Request(object):
    def __init__(self, env, start_response):
        self.env, self.start_response = env, start_response
        self.method = env['REQUEST_METHOD']
        self.pathItems = [x for x in env['PATH_INFO'].split('/') if x != '']
        self.user, self.access = None, 'drwxr-xr-x'
        
    def nextItem(self):
        if self.pathItems:
            item, self.pathItems = self.pathItems[0], self.pathItems[1:]
        else:
            item = None
        return item
        
    # returns (user, None) or (None, '401 Unauthorized')
    def getAuthUser(self, users, realm, addIfMissing=False):
        ''' Authorize OK for now
        hdr = self.env.get('HTTP_AUTHORIZATION', None)
        if not hdr: 
            return (None, '401 Missing Authorization')
        authMethod, value = map(str.strip, hdr.split(' ', 1))
        if authMethod != 'Basic': 
            return (None, '401 Unsupported Auth Method %s'%(authMethod,))
        user, password = base64.b64decode(value).split(':', 1)
        hash_recv = hash(user, realm, password)
        if user not in users: 
            if addIfMissing: 
                users[user] = hash_recv
                return (user, '200 OK')
            else:
                return (user, '404 User Not Found')
        if hash_recv != users[user]: 
            return (user, '401 Not Authorized')
        '''
        user = 'test' # short out the auth for now, make all OK
        return (user, '200 OK')
        
    # throw the 401 response with appropriate header
    def unauthorized(self, realm, reason='401 Unauthorized'):
        self.start_response(reason, [('WWW-Authenticate', 'Basic realm="%s"'%(realm,))])
        raise restlite.Status, reason
    
    def getBody(self):
        try: 
            # Instrument the header
            #print self.env['CONTENT_LENGTH']
            #print self.env['CONTENT_TYPE']
            
            self.env['BODY'] = self.env['wsgi.input'].read(int(self.env['CONTENT_LENGTH']))
            #print self.env['BODY']
 
        except (TypeError, ValueError): 
            raise restlite.Status, '400 Invalid Content-Length'
        if self.env['CONTENT_TYPE'].lower() == 'application/json' and self.env['BODY']: 
            try: 
                self.env['BODY'] = json.loads(self.env['BODY'])                
            except: 
                raise restlite.Status, '400 Invalid JSON content'
        return self.env['BODY']
    
    def verifyAccess(self, user, type, obj):
        return # short out for now
        if not obj: 
            raise restlite.Status, '404 Not Found'
        if '_access' in obj: 
            self.access = obj['_access']
        if '_owner' in obj:
            self.user = obj['_owner']
        index = {'r': 1, 'w': 2, 'x': 3}[type]
        if not (user == self.user and self.access[index] != '-' \
                or user != self.user and self.access[6+index] != '-'):
            raise restlite.Status, '403 Forbidden'
    
            
class RestObject(object):
    def __init__(self, rootObject, users):
        self.rootObject, self.users, self.realm = rootObject, users, 'localhost'
        
    #default GET does simple JSON and XML content negotiation, defaults to JSON   
    def _handleGET(self, currentItem): 
        itemValue = currentItem.get() 
        respType, value = restlite.represent(itemValue, type=self.env.get('ACCEPT', 'application/json'))
        self.start_response('200 OK', [('Content-Type', respType)])
        return value
    
    #default PUT accepts JSON
    def _handlePUT(self, currentItem):
        currentItem.set(self.request.getBody())
        return
    
    #default POST accepts JSON
    def _handlePOST(self, currentItem):
        currentItem.create(self.request.getBody())
        return
    
    def _handleDELETE(self, currentItem):
        currentItem.delete(self.request.getBody())
        return
    
    
    def handler(self, env, start_response):   
        self.env, self.start_response = env, start_response
                    
        print 'restObject.handler()', self.env['SCRIPT_NAME'], self.env['REQUEST_METHOD'], self.env['PATH_INFO'] 
        self.request = Request(self.env, self.start_response)
        
        user, reason = self.request.getAuthUser(self.users, self.realm, addIfMissing=True)
        if not user or not reason.startswith('200'): 
            return self.request.unauthorized(self.realm, reason)
        # step through the path to the endpoint using the nextItem method, verify each resource
        currentResource = self.rootObject
        currentDict = currentResource.resources
        while len(self.request.pathItems) > 1:
            item = self.request.nextItem()
            self.request.verifyAccess(user, 'x', currentDict) # Check "dir" permission for next
            currentDict = currentDict[item].resources # point to next resource dict
        item = self.request.nextItem() #last item in the path should be the resource name

        if item:
            self.request.verifyAccess(user, 'x', currentDict)
            currentResource = currentDict[item]
        if not isinstance(currentResource.resources, dict): # endpoint must have a resources dict for auth info
            raise restlite.Status, '400 Bad Request'
        currentDict = currentResource.resources # make the current dict the endpoint dict for auth info

        if self.request.method == 'POST':
            if item:
                self.request.verifyAccess(user, 'x', currentDict) # create priv
            return self._handlePOST(currentResource)
        
        elif self.request.method == 'PUT':
            if item:
                self.request.verifyAccess(user, 'w', currentDict) # write priv
            return self._handlePUT(currentResource)
        
        elif self.request.method == 'DELETE':
            if item:
                self.request.verifyAccess(user, 'x', currentDict) # create priv
            return self._handleDELETE(currentResource)
        
        elif self.request.method == 'GET':
            if item:
                self.request.verifyAccess(user, 'r', currentDict) # read priv
            return self._handleGET(currentResource)
                
        else: raise restlite.Status, '501 Method Not Implemented'

def bind(objDict, users=None):
    '''The bind method to bind the returned wsgi application to the supplied data and users.
    @param data the original Python data structure which is used and updated as needed.
    @param users the optional users dictionary. If missing, it disables access control.
    @return:  the wsgi application that can be used with restlite.
    '''
    restObject = RestObject(objDict, users)
    def handler(env, start_response):
        return restObject.handler(env, start_response)
    return handler
