'''
Created on Sep 15, 2012

PropertyOfInterest class for exposing custom methods for 
instances of arbitrary types. Typed property pattern

@author: mjkoster
'''
from RESTfulResource import RESTfulResource

class PropertyOfInterest(RESTfulResource):
    
    def __init__(self, parentObject=None, resourceDescriptor = {}):
        RESTfulResource.__init__(self, parentObject, resourceDescriptor)
        