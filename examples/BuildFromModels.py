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
service_metadata = {
    'FQDN': '',
    'IPV4': '',
    'IPV6': ''
    }
#replace with service URIs etc. when starting service instances
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
model_metadata = {
    'objectPath': '',
    'mqttBroker': 'mqtt://localhost:1883'
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

observerTypes = ['subscribers', 'publishers', 'bridges']

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

def createObserver(self, currentResource, observerURI):
    # split by scheme
    # fill in template
    #create resource        
    pass

def graphFromModel(self, model):
    # make rdf-json from the model and parse to RDF graph
    pass


if __name__ == '__main__' :
    
    '''
    make models 
    make list sorted by path length for import from graph, 
    could count a split list but this should be the same if we eat slashes somewhere
    '''
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
                        newChildResource.create(graphFromModel(resourceDescriptor))
                        # FIXME need to aggregate graphs upstream
            # make observers from the list of URIs of each Observer type
            for resourceProperty in resourceDescriptor:
                if resourceProperty in observerTypes:
                    for observerURI in resourceDescriptor[resourceProperty]:
                        createObserver(newResource, observerURI )
    '''
    make services
    '''
    for serviceName in services:
        if services[serviceName]['scheme'] is 'http':
            servicePort = services[serviceName]['port']
            serviceRoot = services[serviceName]['root']
            serviceRootObject = objectFromPath(serviceRoot)
            httpServiceInstance = HttpObjectService(baseObject, port=servicePort)
            
        if services[serviceName]['scheme'] is 'coap':
            servicePort = services[serviceName]['port']
            serviceRoot = services[serviceName]['root']
            serviceRootObject = objectFromPath(serviceRoot)
            coapServiceInstance = CoapObjectService(baseObject, port=servicePort)
                
              
    try:
    # register handlers etc.
        while 1: sleep(1)
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'

    