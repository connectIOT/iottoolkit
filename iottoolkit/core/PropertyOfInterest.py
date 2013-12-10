'''
Created on Sep 15, 2012

PropertyOfInterest class for exposing custom methods for 
instances of arbitrary types. 

get/set expose settings for custom POI instances as in Observers and Agents. 
GET/SET of parent ObservableProperty will access gett and set methods of a POI value property
eg. <ObservablePropertyInstance>.get() will map to <ObservablePropertyInstance>.<PropertyOfInterestInstance>.value.get()
PropertyOfInterest instances register their value methods with the parent ObservableProperty, 
and may register other named property methods to be exposed by the parent OP

FIXME make common code and object for handling settings

@author: mjkoster
'''
from RESTfulResource import RESTfulResource

class PropertyOfInterest(RESTfulResource):
    
    def __init__(self, parentObject=None, resourceDescriptor = {}):
        RESTfulResource.__init__(self, parentObject, resourceDescriptor)
        