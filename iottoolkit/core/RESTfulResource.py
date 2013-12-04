'''
Created on Sep 29, 2012

Base Class for RESTfulResources in SmartObject

Extends the Resource class

This class will be extended by Description, Observers,
ObservableProperty, PropertyOfInterest, and Agent resource classes

Instances of this class are created and deleted from within 
the scope of enclosing classes

Extends the Resource class with methods to parse content-types 
to internal resource representations and to serialize resources 
to content types

@author: mjkoster
'''
from Resource import Resource

class ResourceList(object):
    def __init__(self, listObject):
        self._object = listObject
        self.resources = {}
        
    def get(self, recursive=None):
        self._list = []
        for self._resource in self._object.resources: #only list child objects
            if self._resource not in ('l', 'Properties', 'thisObject', 'baseObject', 'parentObject' ):
                self._list.append({'resourceName': self._object.resources[self._resource].Properties.get('resourceName'), \
                                   'resourceClass': self._object.resources[self._resource].Properties.get('resourceClass')})
        return self._list
    
class RESTfulDictEndpoint(object): # create a resource endpoint from a property reference
    def __init__(self, dictReference):
        self.resources = {}
        self._resource = dictReference # this only happens on init of the RESTfulEndpoint
    #try the Property interface to expose the dictionary with getter and setter properties
    @property
    def dict(self):
        return self._resource
    @dict.setter
    def dict(self, dictUpdate):
        self._resource.update(dictUpdate)

    def get(self, key=None):
        if key == None:
            return self._resource
        else:
            return self._resource[key]
    
    def getList(self, key=None):
        if key == None:
            return self._resource.keys()
        else:
            return self._resource[key]
        
    def set(self,dictUpdate):
        self._resource.update(dictUpdate)
        return

    def update(self,dictUpdate):
        self._resource.update(dictUpdate)
        return
    
    #try the decsriptor interface to allow use of the attribute as a reference
    def __get__(self, instance, owner=None):
        return self._resource
    
    def __set__(self, instance, dictUpdate):
        self._resource.update(dictUpdate)
        return
    

class RESTfulResource(Resource) :    
    # when this resource is created
    def __init__(self, parentObject=None, resourceDescriptor = {}):
        Resource.__init__(self)
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
        
    # new create takes dictionary built from JSON object POSTed to parent resource
    def create(self, resourceDescriptor):
        resourceName = resourceDescriptor['resourceName']
        resourceClass = resourceDescriptor['resourceClass']
        if resourceName not in self.resources:
            # create new instance of the named class and add to resources directory, return the ref
            self.resources.update({resourceName : globals()[resourceClass](self, resourceDescriptor)}) 
        return self.resources[resourceName] # returns a reference to the created instance
                        
     
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


