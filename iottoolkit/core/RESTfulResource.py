'''
Created on Sep 29, 2012

Base Class for RESTfulResources in SmartObject

This class will be extended by Description, Observers,
ObservableProperty, PropertyOfInterest, and Agent resource classes

Instances of this class are created and deleted from within 
the scope of enclosing classes

Extends the Resource class with methods to parse content-types 
to internal resource representations and to serialize resources 
to content types

@author: mjkoster
'''
import json

class ResourceList(object):
    def __init__(self, listObject):
        #FIXME LinkFormatProxy isn't a container but want to avoid using GET to make constructor
        self._containerClasses = ['SmartObject', 'Observers', 'Agent', 'LinkFormatProxy' , 'ObservableProperty' ]
        self._derivedResources = ['l', 'Properties', 'Resources', 'thisObject', 'baseObject', 'parentObject' ]
        self._object = listObject
        self.resources = {}
        
        
    def get(self):
        return self._listRecursive(self._object)
    
    # to enable create-on-publish
    def set(self, objectGraph):
        self._buildRecursive(self._object, objectGraph)
    
    # normal create
    # object graph is the python list of constructor dictionaries with their lists etc that results from json.loads
    def create(self, objectGraph):
        self._buildRecursive(self._object, objectGraph)
                           
    def _listRecursive(self, object): #Serialize the object tree below this object to JSON
        resources = object.resources
        resourceList=[]
        for resource in resources: #only list child objects
            if resource not in self._derivedResources:
                childObject=resources[resource]
                resourceName = childObject.Properties.get('resourceName')
                resourceClass = childObject.Properties.get('resourceClass')
                resourceConstructor = {'resourceName': resourceName, \
                                       'resourceClass': resourceClass}
                if resourceClass in self._containerClasses:
                    # go down into containers
                    resourceList.append([ resourceConstructor , self._listRecursive(childObject) ] )
                else:
                    if resourceClass == 'Description': 
                        # have rdf-json serializer make JSON and then python structure to pack into the big graph
                        graph = json.loads( childObject.serialize(childObject.get(),'application/json') )
                        resourceConstructor.update({'graph' : graph })
                    else:
                        resourceConstructor.update(childObject.get())
                    resourceList.append([resourceConstructor])
        return resourceList
   
    def _buildRecursive(self, currentObject, constructorList):
        # objectGraph is a reference to a list of lists of resource constructors, some of which are containers
        # walk the list of objects and recursively descend into containers
        for newList in constructorList:
            newConstructor = newList[0]
            if newConstructor != None : 
                newObject = currentObject.create(newConstructor) # the object constructor
                if newConstructor['resourceClass'] in self._containerClasses:
                    # descend into container
                    self._buildRecursive(newObject, newList[1]) # the object's list of sub-objects (resources)

   
class RESTfulDictEndpoint(object): # create a resource endpoint from a property reference
    def __init__(self, dictReference):
        self.resources = {} # the recursive router likes to see an empty link dictionary to indicate endpoint
        self._resource = dictReference # this only happens on init of the RESTfulEndpoint
    #try the Property interface to expose the dictionary with getter and setter properties
    @property
    def dict(self):
        return self._resource
    @dict.setter
    def dict(self, dictUpdate):
        self._resource.update(dictUpdate)

    def get(self, key=None):
        # FIXME derive key from query
        if key == None:
            return self._resource
        else:
            return self._resource[key]
    
    def getList(self, key=None):
        # FIXME derive key from query
        if key == None:
            return self._resource.keys()
        else:
            return self._resource[key]
        
    def set(self,dictUpdate):
        # set maps to update
        self._resource.update(dictUpdate)
        return

    def update(self,dictUpdate):
        self._resource.update(dictUpdate)
        # could add hook here for dict update side effect
        return
        
    #try the decsriptor interface to allow use of the attribute as a reference
    def __get__(self, instance, owner=None):
        return self._resource
    
    def __set__(self, instance, dictUpdate):
        self._resource.update(dictUpdate)
        return
    

class RESTfulResource(object) :    
    # when this resource is created
    def __init__(self, parentObject=None, resourceDescriptor = {}):
        self.resources = {} # the visible directory of resource names 
        self.value = []
        # The resources dictionary is for subclasses of RESTfulResource, routable as http endpoints
        # The Properties dictionary is for serializable objects and strings, get/put but not routable
        self.Resources = RESTfulDictEndpoint(self.resources) #make resources endpoint from the dictionary
        # make properties resource and it's endpoint
        self._properties = {}
        self.Properties = RESTfulDictEndpoint(self._properties) #make Properties endpoint from its dict
        # make an entry in resources to point to properties
        self.Resources.update({'Properties': self.Properties}) # put Properties into the resource dict
        self.Resources.update({'thisObject': self}) #self-identity
        # initialize Properties by putting in the constructor properties
        
        self._resourceDescriptor = resourceDescriptor # for settings and properties update

        if parentObject == None : #no parent means this is a base object, fill in base settings
            self.Resources.update({'baseObject': self})
            self.Resources.update({'parentObject': self})
            self.Properties.update({'pathFromBase': ''})
            self.Properties.update({'resourceName': 'baseObject'})
            self.Properties.update({'resourceClass': 'SmartObject'})
        else : # fill in properties and identity of parent, base, and path to base
            self.Properties.update({'resourceName': resourceDescriptor['resourceName']}) 
            self.Properties.update({'resourceClass': resourceDescriptor['resourceClass']})
            self.Resources.update({'parentObject' : parentObject.Resources.get('thisObject')})
            self.Resources.update({'baseObject': parentObject.Resources.get('baseObject') })
            self.Properties.update({'pathFromBase': self.Resources.get('parentObject').Properties.get('pathFromBase') \
                                   + '/' + self.Properties.get('resourceName')})
            
        self._parseContentTypes = ['*/*'] 
        self._serializeContentTypes = ['*/*']
        self.defaultResources = None
        
        self.resources.update({'l': ResourceList(self)})
        
    # return the default contents of this resource
    def get(self) :
        return self._get() 
    
    def _get(self) :
        return self.value 
    
    # update the default contents of this resource
    def set(self, newValue) :
        self._set(newValue)
        return

    def _set(self, newValue) :
        self.value=newValue
        return
        
    # new create takes dictionary built from JSON object POSTed to parent resource
    def create(self, resourceDescriptor):
        resourceName = resourceDescriptor['resourceName']
        resourceClass = resourceDescriptor['resourceClass']
        if resourceName not in self.resources:
            # create new instance of the named class and add to resources directory, return the ref
            self.resources.update({resourceName : globals()[resourceClass](self, resourceDescriptor)}) 
        return self.resources[resourceName] # returns a reference to the created instance
                        
    # for removing resources inside this resource
    def delete(self, resourceName) :
        # notify the resource that it's being deleted
        self.resources[resourceName].cleanupRecursive()
        #
        # force dereference the object
        #
        # unlinks the resource 
        del self.resources[resourceName] # remove dict entry FIXME remove reference to instance
        return
     
    def cleanupRecursive(self):
        # clean up, dereference, and unlink all child resources recursively
        #
        self._cleanup() # terminate threads and release resources
        #
        # recursively clean up, dereference, and unlink
        for resource in self.resources:
            #
            self.resources[resource].cleanupRecursive()
            #
            # force dereference the object
            #
            # unlink the resource
            del self.resources[resource]
    
    def _cleanup(self):
        # override this in derived classes to terminate threads and release resources
        pass
     
""" Default representation is JSON, XML also supported
    Add parse and serialize for RDF graph, etc. for richer 
    representation than JSON
    # Convert representation to native type
    def parse(self, content) :
        def types(self):
            return(self.parserContent_types)
        return content.value ;

    # Convert native type to representation
    def serialize(self, resource) :
        def types(self):
            return(self.serializerContent_types)
        return resource.str
"""


