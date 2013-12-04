'''
Created on Sep 15, 2012

Agent classes. Contains reference to instance of class containing observer 
handlers and code 

Agent Instances are created automatically. Create a named Handler instance under the Agent, 
as an instance of the desired handler class, optionally specifying a module path setting {'classPath': '<path_to_module>'}
by PUT (set) of a JSON object containing a dictionary of settings

for example myObserver.set({'handlerClass': 'SmartObject.Agent.additionHandler'})

@author: mjkoster
'''


from RESTfulResource import RESTfulResource

class Handler(RESTfulResource):   # single base class for handlers to extend directly, contains convenience methods for linking resources
    def __init__(self, parentObject=None, resourceDescriptor = {}):
        RESTfulResource.__init__(self, parentObject, resourceDescriptor)
        self._settings = self._resourceDescriptor # use the constructor descriptor for the initial settings
        # link cache keeps endpoints hashed by pathFromBase string, only need to walk the path one time
        self._linkBaseDict = self.Resources.get('baseObject').resources
        self._linkCache = {}
        self._init()
        
    def _init(self):
        pass
          
    def get(self, Key=None):
        if Key != None :
            return self._settings[Key]
        else :
            return self._settings
     
    def set(self, newSettings): # create an instance of a handler from settings dictionary
        self._settings.update(newSettings)

    def handleNotify(self, updateRef=None): # external method to call from Observer-Notifier
        self._handleNotify(updateRef)
    
    def _handleNotify(self, updateRef=None ): # override this for handling state changes from an observer
        pass

    def linkToRef(self, linkPath):
        '''
        takes a path string and walks the object tree from a base dictionary
        returns a ref to the resource at the path endpoint
        store translations in a hash cache for fast lookup after the first walk
        '''
        self._linkPath = linkPath
        if self._linkPath in self._linkCache.keys() :
            return self._linkCache[self._linkPath]
        # cache miss, walk path and update cache at end
        self._currentDict = self._linkBaseDict
        self._pathElements = linkPath.split('/')
        for pathElement in self._pathElements[:-1] : # all but the last, which should be the endpoint
            self._currentDict = self._currentDict[pathElement].resources
        self._resource = self._currentDict[self._pathElements[-1] ]
        self._linkCache.update({ self._linkPath : self._resource })
        return self._resource
        
    def getByLink(self, linkPath):
        return self.linkToRef(linkPath).get()

    def setByLink(self, linkPath, newValue):
        self.linkToRef(linkPath).set(newValue)


class addHandler(Handler): # an example appHandler that adds two values together and stores the result
    # define a method for handling state changes in observed resources       
    def _handleNotify(self, updateRef = None ):
        # get the 2 addends, add them, and set the sum location
        self._addend1 = self.getByLink(self._settings['addendLink1'])
        self._addend2 = self.getByLink(self._settings['addendLink2'])
        self.setByLink( self._settings['sumOutLink'], self._addend1 + self._addend2 )


# simple print handler that echoes the value each time an observed resource is updated
class logPrintHandler(Handler):
    def _handleNotify(self, resource) :
        print resource.Properties.get('resourceName'), ' = ', resource.get()
 

class Agent(RESTfulResource):
    # Agent is a container for Handlers and daemons, instantiated as a resource of a SmartObject 
    def __init__(self, parentObject=None, resourceDescriptor = {}):
        RESTfulResource.__init__(self, parentObject, resourceDescriptor)
        self._handlers = {}
        
    def get(self, handlerName=None):
        if handlerName == None:
            return self._handlers # to get the list of names
        else:
            if self._handlers.has_key(handlerName) :
                return self._handlers[handlerName] # to get reference to handler resources by handler name
        return None
    
    # new create takes dictionary built from JSON object POSTed to parent resource
    def create(self, resourceDescriptor):
        resourceName = resourceDescriptor['resourceName']
        resourceClass = resourceDescriptor['resourceClass']
        # import the module if it's specified in the descriptor
        if resourceDescriptor.has_key('resourceClassPath') : 
            resourceClassPath = resourceDescriptor['resourceClassPath'] 
            self.importByPath(resourceClassPath)
        
        if resourceName not in self.resources:
            # create new instance of the named class and add to resources directory, return the ref
            self.resources.update({resourceName : globals()[resourceClass](self, resourceDescriptor)}) 
            #pass the constructor the entire descriptor for creating the properties object
            #self.resources.update({resourceName : globals()[resourceClass](self, resourceDescriptor)}) 
            self._handlers.update({resourceName: resourceClass})
        return self.resources[resourceName] # returns a reference to the created instance
                 
        # need to destroy instance of code module
        
    # FIXME Doesn't seem to work. Need to look at this and recursive import issue, devise dynamic import system 
    def importByPath(self,classPath):
        # separate the module path from the class,import the module, and return the class name
        self._components = classPath.split('.')
        self._module = __import__( '.'.join(self._components[:-1]) )
        return self._module
            
        