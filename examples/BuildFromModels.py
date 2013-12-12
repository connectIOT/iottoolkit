'''
Created on Dec 12, 2013

Create services from a service model instance, create objects from an object model instance 
How are base objects mapped to services? 
This file creates a service object that has multiple services and a single object tree
There could be a service creation service where POSTing this descriptor would 

@author: mjkoster
'''
from interfaces.HttpObjectService import HttpObjectService
from interfaces.CoapObjectService import CoapObjectService

from core.SmartObject import SmartObject
from core.Description import Description
from core.ObservableProperty import ObservableProperty
from core.Observers import Observers
from core.PropertyOfInterest import PropertyOfInterest
from rdflib.term import Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, OWL
from interfaces.HttpObjectService import HttpObjectService
from interfaces.CoapObjectService import CoapObjectService
from time import sleep
import sys


#workaround to register rdf JSON plugins 
import rdflib
from rdflib.plugin import Serializer, Parser
rdflib.plugin.register('json-ld', Serializer, 'rdflib_jsonld.serializer', 'JsonLDSerializer')
rdflib.plugin.register('json-ld', Parser, 'rdflib_jsonld.parser', 'JsonLDParser')
rdflib.plugin.register('rdf-json', Serializer, 'rdflib_rdfjson.rdfjson_serializer', 'RdfJsonSerializer')
rdflib.plugin.register('rdf-json', Parser, 'rdflib_rdfjson.rdfjson_parser', 'RdfJsonParser')

'''
model format for populating Description and creating SmartObject instances and service instances
'''
services = {
    'localHTTP' : {
        'scheme': 'http',
        'FQDN': 'localhost',
        'port': 8000,
        'IPV4': '',
        'root': '/',
        'discovery': '/'
                    },
                
    'localCoAP': {
        'scheme': 'coap',
        'FQDN': 'localhost',
        'port': 5683,
        'IPV4': '',
        'root': '/',
        'discovery': '/' 
                    }
             }

"""
Minimal server needs one base object 
Starting a server will create one but this provides a discoverable model and container

models = {
    '/': {
        'resourceName': '/',
        'resourceClass': 'SmartObject'
        },
    }
"""    
models = {
    '/': {
        'resourceName': '/',
        'resourceClass': 'SmartObject'
        },
    '/sensors': {
        'resourceName': 'sensors',
        'resourceClass': 'SmartObject'
        },
    '/sensors/rhvWeather-01': {
        'resourceName': 'rhvWeather-01',
        'resourceClass': 'SmartObject'
        },
    '/sensors/rhvWeather-01/indoor_temperature': {
        'resourceName': 'indoor_temperature',
        'resourceClass': 'ObservableProperty',
        'resourceType': 'temperature',
        'interfaceType':'sensor',
        'subscribers': ['mqtt://smartobjectservice.com:1883/sensors/rhvWeather-01/indoor_temperature'],
        'publishers': '',
        'bridges': ''
        }
    }

mqttObserverTemplate = {
    'resourceName': 'mqttObserver',
    'resourceClass': 'mqttObserver',
    'connection': 'localhost',
    'pubTopic': '',
    'subTopic': ''
    }

httpPublisherTemplate = {
    'resourceName': 'httpPublisher',
    'resourceClass': 'httpPublisher',
    'connection': 'localhost'
    }

httpSubscriberTemplate = {
    'resourceName': 'httpSubscriber',
    'resourceClass': 'httpSubscriber',
    'connection': 'localhost',
    }

callbackNotifierTemplate = {
    'resourceName': 'callbackNotifier',
    'resourceClass': 'callbackNotifier',
    'handlerURI': 'localhost'
    }

observerSchemes = ['http', 'coap', 'handler', ]

defaultResources = {
    'SmartObject': ['Description', 'Agent'],
    'ObservableProperty': ['Description', 'Observers']
    }

baseObject = None

def objectFromPath(self,path, baseObject):
    currentObject=baseObject
    for pathElement in path.split('/')[:-1]:
        currentObject=object.resources[pathElement]
    return currentObject

def createByScheme(self, currentResource, resourceDescriptor):
    pass

def graphFromModel(self, model):
    pass


if __name__ == '__main__' :
    # make models first
    # make list sorted by path length for import from graph, 
    # could count a split list but this should be the same if we eat slashes somewhere
    resourceList = sorted( models.keys(), key=str.count('/') )
    
    for resource in resourceList:
        resourceDescriptor = models[resource]
        # see if base object needs to be created. 
        if resource is '/' and resourceDescriptor['resourceClass'] is 'SmartObject' and baseObject is None:
            baseObject = SmartObject()
        else:
            newResource = objectFromPath(resource).create(resourceDescriptor)
            if resourceDescriptor['resourceClass'] in defaultResources:
                for defaultResource in defaultResources[resource]:
                    newChildResource = newResource.create({
                                        'resourceName': defaultResource,
                                        'resourceClass': defaultResource
                                        })
                    if defaultResource is 'Description': 
                        newChildResource.set(graphFromModel(resourceDescriptor))
                    
                    
            # set description and propagate back up to root
            newResource.Description.create(resourceDescriptor)
            # make observer instances and agent instances
            createByScheme(newResource, resourceDescriptor)
            
    
    # make an empty instance of a SmartObject shared by 2 interfaces, 
    # CoAP and HTTP, default object root and default ports 5683 and 8000
    # CoAP service makes the base object and it is passed to the http service constructor
    
    baseObject = HttpObjectService( CoapObjectService().baseObject ).baseObject
    
    # emulate the .well-known/core interface
    baseObject.create({'resourceName': '.well-known','resourceClass': 'SmartObject'},\
                        ).create({'resourceName': 'core','resourceClass': 'LinkFormatProxy'})
          
    try:
    # register handlers etc.
        while 1: sleep(1)
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'

    