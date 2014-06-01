'''
Created on Dec 12, 2013

Create services from a service model instance, create objects from an object model instance 
How are base objects mapped to services? 
This file creates a service object that has multiple services and a single object tree
There could be a service creation service where POSTing this descriptor would build objects 
and create service instance, and this will be built as function sets, probably part of 
Resource Directory (RD)

@author: mjkoster
'''
from core.RESTfulResource import RESTfulResource
from core.SmartObject import SmartObject
from core.Description import Description
from core.ObservableProperty import ObservableProperty
from core.Observers import Observers
from core.PropertyOfInterest import PropertyOfInterest
from rdflib.term import Literal, URIRef
from interfaces.HttpObjectService import HttpObjectService
from interfaces.CoapObjectService import CoapObjectService
from time import sleep
from urlparse import urlparse
import sys
import subprocess
import rdflib

#workaround to register rdf JSON plugins 
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
#replace with unique service URIs e.g. http://localhost:8000  when starting service instances
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

object_metadata = {
    'objectPath': '',
    }

objects = {
    '/': {
        'resourceName': '/',
        'resourceClass': 'SmartObject'
        },
    '/services': {
        'resourceName': 'services',
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
    '/sensors/rhvWeather-01/outdoor_temperature': {
        'resourceName': 'outdoor_temperature',
        'resourceClass': 'ObservableProperty',
        'resourceType': 'temperature',
        'interfaceType':'sensor',
        'subscriber': ['mqtt://smartobjectservice.com:1883/sensors/rhvWeather-01/outdoor_temperature'],
        'publisher': '',
        'bridge': ''
        },
    '/sensors/rhvWeather-01/outdoor_humidity': {
        'resourceName': 'outdoor_humidity',
        'resourceClass': 'ObservableProperty',
        'resourceType': 'humidity',
        'interfaceType':'sensor',
        'subscriber': ['mqtt://smartobjectservice.com:1883/sensors/rhvWeather-01/outdoor_humidity'],
        'publisher': '',
        'bridge': ''
        }
    }


class SystemInstance(object):
    '''
    creates service instances and object instances from dictionary constructors
    {
    'service_metadata': {},
    'services': {},
    'object_metadata': {},
    'objects': {}
    }
    '''
    def __init__(self, systemConstructor):
        
        self._service_metadata = systemConstructor['service_metadata']
        self._services = systemConstructor['services']
        self._object_metadata = systemConstructor['object_metadata']
        self._objects = systemConstructor['objects']
        
        self._baseObject = None
        
        self._defaultResources = {
                                  'SmartObject': ['Description', 'Agent'],
                                  'ObservableProperty': ['Description', 'Observers']
                                  }

        self._observerTypes = ['subscriber', 'publisher', 'bridge']
        
        self._observerSchemes = ['http', 'coap', 'mqtt', 'handler']

        self._mqttObserverTemplate = {
                                      'resourceName': 'mqttObserver',
                                      'resourceClass': 'mqttObserver',
                                      'connection': 'localhost',
                                      'pubTopic': '',
                                      'subTopic': '',
                                      'keepAlive': 60,
                                      'QoS': 0
                                      }
        
        self._httpPublisherTemplate = {
                                       'resourceName': 'httpPublisher',
                                       'resourceClass': 'httpPublisher',
                                       'targetURI': 'http://localhost:8000/'
                                       }
        
        self._httpSubscriberTemplate = {
                                        'resourceName': 'httpSubscriber',
                                        'resourceClass': 'httpSubscriber',
                                        'ObserverURI': 'http://localhost:8000/',
                                        }
        
        self._coapPublisherTemplate = {
                                       'resourceName': 'coapPublisher',
                                       'resourceClass': 'coapPublisher',
                                       'targetURI': 'coap://localhost:5683/'
                                       }
        
        self._coapSubscriberTemplate = {
                                        'resourceName': 'coapSubscriber',
                                        'resourceClass': 'coapSubscriber',
                                        'connection': 'coap://localhost:5683/'
                                        }

        self._callbackNotifierTemplate = {
                                          'resourceName': 'callbackNotifier',
                                          'resourceClass': 'callbackNotifier',
                                          'handlerURI': 'handler://'
                                          }

        '''
        make objects from object models first
        make list sorted by path element count + length for import from graph, 
        could count a split list but this should be the same if we eat slashes somewhere
        having the root object called '/' and '/' as the separator is extra work 
        '''
        self._resourceList = sorted( self._objects.keys(), key=lambda s:s.count('/') )
        self._resourceList = sorted( self._resourceList, key=lambda s:len(s))
        for self._resourceLink in self._resourceList:
            self._resourceDescriptor = self._objects[self._resourceLink]
            # see if base object needs to be created. 
            if self._resourceLink is '/' and self._resourceDescriptor['resourceClass'] is 'SmartObject' and self._baseObject is None:
                self._newResource = SmartObject()
                self._baseObject = self._newResource
            else:
                self._parentLink = '/'.join(self._resourceLink.split('/')[:-1])
                if self._parentLink == '': self._parentLink = '/'
                self._parentObject = self._objectFromPath(self._parentLink, self._baseObject)
                self._newResource = self._parentObject.create( self._resourceDescriptor)
            if self._resourceDescriptor['resourceClass'] in self._defaultResources:
                for self._defaultResource in self._defaultResources[self._resourceDescriptor['resourceClass']]:
                    self._newChildResource = self._newResource.create({
                                        'resourceName': self._defaultResource,
                                        'resourceClass': self._defaultResource
                                        })
                    if self._defaultResource is 'Description': 
                        self._newChildResource.create(self._graphFromModel(self._resourceLink, self._resourceDescriptor))
                        # FIXME need to aggregate graphs upstream
            # make observers from the list of URIs of each Observer type
            for self._resourceProperty in self._resourceDescriptor:
                if self._resourceProperty in self._observerTypes:
                    for self._observerURI in self._resourceDescriptor[self._resourceProperty]:
                        self._observerFromURI(self._newResource, self._resourceProperty, self._observerURI )
        '''
        make services
        '''
        # make this a service Object (RESTfulResource) with dict as constructor
        self._serviceRegistry = self._objectFromPath('/services', self._baseObject)
        self._serviceDescription = self._objectFromPath('/services/Description', self._baseObject)        
    
        for self._serviceName in self._services:
            self._newService = ServiceObject(self._serviceName, self._services[self._serviceName], self._serviceRegistry)
            self._serviceRegistry.resources.update({self._serviceName:self._newService})
            self._serviceDescription.set(self._graphFromModel(self._serviceName, self._services[self._serviceName]))
            
            
    def _graphFromModel(self, link, meta):
        # make rdf-json from the model and return RDF graph for loading into Description
        g=rdflib.Graph()
        subject=URIRef(link)
        for relation in meta:
            value = meta[relation]
            g.add((subject, Literal(relation), Literal(value)))
        return g

    def _observerFromURI(self, currentResource, observerType, observerURI):
        # split by scheme
        URIObject=urlparse(observerURI)
        # fill in constructor template
        if URIObject.scheme == 'http':
            if observerType is 'publisher':
                resourceConstructor = self._httpPublisherTemplate.copy()
                resourceConstructor['targetURI'] = observerURI
            if observerType is 'subscriber':
                resourceConstructor = self._httpSubscriberTemplate.copy()
                resourceConstructor['observerURI'] = observerURI
    
        elif URIObject.scheme == 'coap':
            if observerType is 'publisher':
                resourceConstructor = self._coapPublisherTemplate.copy()
                resourceConstructor['targetURI'] = observerURI
            if observerType is 'subscriber':
                resourceConstructor = self._coapSubscriberTemplate.copy()
                resourceConstructor['observerURI'] = observerURI
    
        elif URIObject.scheme == 'mqtt':
            resourceConstructor = self._mqttObserverTemplate.copy() 
            resourceConstructor['connection'] = URIObject.netloc
            if observerType is 'publisher':
                resourceConstructor['pubTopic'] = URIObject.path
            if observerType is 'subscriber':
                resourceConstructor['subTopic'] = URIObject.path
            if observerType is 'bridge':
                resourceConstructor['pubTopic'] = URIObject.path
                resourceConstructor['subTopic'] = URIObject.path

        elif URIObject.scheme == 'handler':
            resourceConstructor = self._callbackNotifierTemplate.copy()   
            resourceConstructor['handlerURI'] = observerURI
            
        else:
            print 'no scheme', URIObject.scheme
            return
            
        #create resource in currentResource.resources['Observers'] container  
        newObserver = currentResource.resources['Observers'].create(resourceConstructor) 

    def _objectFromPath(self, path, baseObject):
    # fails if resource doesn't exist
        currentObject=baseObject
        pathList = path.split('/')[1:]
        for pathElement in pathList:
            if len(pathElement) > 0:
                currentObject=currentObject.resources[pathElement]
        return currentObject

class ServiceObject(RESTfulResource):
    def __init__(self, serviceName, serviceConstructor, baseObject):
        self._resourceConstructor = {
                               'resourceName': serviceName,
                               'resourceClass': serviceConstructor['scheme']
                               }
        
        RESTfulResource.__init__(self, baseObject, self._resourceConstructor )
        self._serviceConstructor = serviceConstructor
        # TODO collect IP addresses and update the constructor
        if self._serviceConstructor['scheme'] is 'http':
            self._httpService = HttpObjectService\
            (self._objectFromPath(self._serviceConstructor['root'], baseObject), port=self._serviceConstructor['port'])
            URLObject= urlparse(self._httpService._baseObject.Properties.get('httpService'))
            self._serviceConstructor['FQDN'] = URLObject.netloc.split(':')[0]
            
        if self._serviceConstructor['scheme'] is 'coap':
            self._coapService = CoapObjectService\
            (self._objectFromPath(self._serviceConstructor['root'], baseObject), port=self._serviceConstructor['port'])
            URLObject= urlparse(self._coapService._baseObject.Properties.get('coapService'))
            self._serviceConstructor['FQDN'] = URLObject.netloc.split(':')[0]
                
        if serviceConstructor['scheme'] is 'mqtt':
            subprocess.call('mosquitto -d -p ', self._serviceConstructor['port'])
            
        self._set(self._serviceConstructor)

    def _objectFromPath(self, path, baseObject):
    # fails if resource doesn't exist
        currentObject=baseObject
        pathList = path.split('/')[1:]
        for pathElement in pathList:
            if len(pathElement) > 0:
                currentObject=currentObject.resources[pathElement]
        return currentObject


if __name__ == '__main__' :
    '''
    make an instance using the example constructors
    '''
    systemConstructor = {'service_metadata': service_metadata,
                             'services': services,
                             'object_metadata': object_metadata,
                             'objects': objects
                             }
    
    system = SystemInstance(systemConstructor)
    
    print system._baseObject.resources['services'].resources['localHTTP'].get()
    print system._baseObject.resources['services'].resources['localCoAP'].get()
              
    try:
    # register handlers etc.
        while 1: sleep(1)
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'

    