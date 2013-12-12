'''
Created on Dec 12, 2013

Create services from a service model instance, create objects from an object model instance 

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
        'resourceClass': 'SmartObject',
        'resourceType': 'temperature',
        'interfaceType':'sensor',
        'subscribeURI': 'mqtt://smartobjectservice.com:1883/sensors/rhvWeather-01/indoor_temperature',
        'publishURI': '',
        'bridgeURI': ''
        }
    }

def objectFromPath(self,path, scope=None):
    if scope=='parent':
        pass
        
    return

if __name__ == '__main__' :
    
    # make models first
    baseObject = None
    # make list and sort by path length for import from graph
    resourceList = models
    
    for resource in resourceList:
        resourceDescriptor = resourceList[resource]
        if resource is '/' and resourceDescriptor['resourceClass'] is 'SmartObject' and baseObject is None:
            baseObject = SmartObject()
        else:
            resourceConstructor = resourceDescriptor
            objectFromPath(resource, scope ='parent').create(resourceConstructor)
    
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

    