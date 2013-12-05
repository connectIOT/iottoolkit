'''
Created on Sep 15, 2012

Base Class for Resources in SmartObject

This class will be extended by RESTfulResource to add content-type support

Contains methods for resource-oriented services:
create, delete, set, and get are meant to be 
extended or overridden by concrete class instances 
for content-specific interaction

@author: mjkoster
'''
class Resource(object) :
    
    # when this resource is created
    def __init__(self):
        self.resources = {} # the visible directory of resource names 
        self.value = []

    # when this resource is deleted, recursively delete all internal resources
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

    def create(self, resourceName, className) :
        return self._create(resourceName, className)
      
    # for adding resources inside this resource
    def _create(self, resourceName, className) :
        # create new instance of the named class and add to resources directory, return the ref
        self.resources.update({resourceName : globals()[className]()}) 
        return self.resources[resourceName]
    
    # for removing resources inside this resource
    def delete(self, resourceName) :
        del self.resources[resourceName] # remove dict entry FIXME remove reference to instance
        return
