'''
Created on Sep 15, 2012

SmartObject class

The SmartObject is the top level Resource pointed to by the URL

The base resource is a description, which for linked data is the default
resource returned by SmartObject.get() 

Practical instances of SmartObject will have additional resources 
such as ObservableProperty and Agent instances dynamically created
from resource constructors loaded into the top level Description resource 

Clone and composite SmartObject instances can be built from resource 
constructors of other SmartObjects

@author: mjkoster
'''
from RESTfulResource import RESTfulResource
from Description import Description
from Agent import Agent
from ObservableProperty import ObservableProperty
from Observers import Observers
from PropertyOfInterest import PropertyOfInterest
from LinkFormatProxy import LinkFormatProxy

class SmartObject(RESTfulResource):
    
    def __init__(self, parentObject=None, resourceDescriptor = {}):
        RESTfulResource.__init__(self, parentObject, resourceDescriptor)
        # make the defaultResources
        self.Description = self.create({'resourceName':'Description',\
                                        'resourceClass': 'Description'})
        self.Agent = self.create({'resourceName':'Agent',\
                                  'resourceClass':'Agent'})            

    def get(self):
        if 'Description' in self.resources :
            return self.resources['Description'].get()
        return None
    
    def set(self, (s,p,o)): 
        if 'Description' in self.resources :
            self.resources['Description'].set((s,p,o))
            
    def create(self, resourceDescriptor):
        resourceName = resourceDescriptor['resourceName']
        resourceClass = resourceDescriptor['resourceClass']
        if resourceName not in self.resources:
            # create new instance of the named class and add to resources directory, return the ref
            self.resources.update({resourceName : globals()[resourceClass](self, resourceDescriptor)}) 
        return self.resources[resourceName] # returns a reference to the created instance

    def serialize(self, graph, cType) : 
        if 'Description' in self.resources :
            return self.resources['Description'].serialize(graph, cType)
        return None
    
    def serializeContentTypes(self) :
        if 'Description' in self.resources :
            return self.resources['Description'].serializeContentTypes()
        return None
        
        