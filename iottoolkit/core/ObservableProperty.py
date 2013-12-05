'''
Created on Sep 15, 2012

ObservableProperty class to hold the PropertyOfInterest and it's description 
and potential observers

The Descriptor Property is the ObservableProperty, 
which has it's value as it's Descriptor Property
allowing the value of the ObservableProperty to be 
it's Descriptor Property

Thus the value of a smart object Observable Properties 
can be referenced by <SmartObject>.<ObservableProperty>
e.g.:

display(room.temperature) 
"room" is the name of the SmartObject and "temperature" is the name of an 
ObservableProperty of the "room" object

thermostat.setting = 77
"thermostat" is the name of the object and "setting" is the name of the
ObservableProperty being manually set

@author: mjkoster
'''
from RESTfulResource import RESTfulResource
from PropertyOfInterest import PropertyOfInterest
from Description import Description
from Observers import Observers

class ObservableProperty(RESTfulResource):
    
    def __init__(self, parentObject=None, resourceDescriptor = {}):
        RESTfulResource.__init__(self, parentObject, resourceDescriptor) 
        #make default resources
        self.Description = self.create({'resourceName':'Description',\
                                        'resourceClass': 'Description'})
        self.Observers = self.create({'resourceName':'Observers',\
                                  'resourceClass':'Observers'})            
        
    def get(self):
        if 'PropertyOfInterest' in self.resources : # allow creation of a custom object mapped to the observable property
            return self.resources['PropertyOfInterest'].get()
        else :
            return self._get()
    
    def set(self, newValue):
        if 'PropertyOfInterest' in self.resources :
            self.resources['PropertyOfInterest'].set(newValue)
        else :
            self._set(newValue) # if no POI is created, use the base class set method
            
        if 'Observers' in self.resources :
            self.resources['Observers'].onUpdate(self) # invoke the onUpdate routine 

    # new create takes dictionary built from JSON object POSTed to parent resource
    def create(self, resourceDescriptor):
        resourceName = resourceDescriptor['resourceName']
        resourceClass = resourceDescriptor['resourceClass']
        if resourceName not in self.resources:
            # create new instance of the named class and add to resources directory, return the ref
            self.resources.update({resourceName : globals()[resourceClass](self, resourceDescriptor)}) 
        return self.resources[resourceName] # returns a reference to the created instance

