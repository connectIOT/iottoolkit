'''
Created on July 26, 2013

Simplified weather sensor subscribe to broker with 2 endpoints
Creates second service to test object creation from JSON

@author: mjkoster
'''
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
rdflib.plugin.register('rdf-json', Parser, 'rdflib_rdfjson.rdfjson_parser', 'RdfJsonSerializer')


if __name__ == '__main__' :
    
    baseObject = HttpObjectService().baseObject # make an instance of the service, default object root and default port 8000
    
    coapService = CoapObjectService(baseObject)

    # create a second service port with an empty default base object to test create from JSON
    HttpObjectService(port=8001)
    
    # create the weather station resource template
    # emulate the .well-known/core interface
    baseObject.create({'resourceName': '.well-known','resourceClass': 'SmartObject'},\
                        ).create({'resourceName': 'core','resourceClass': 'LinkFormatProxy'})
      
    # sensors resource under the baseObject for all sensors  
    # top level object container for sensors, default class is SmartObject  
    sensors = baseObject.create({'resourceName': 'sensors', 'resourceClass': 'SmartObject'}) 
  
    #weather resource under sensors for the weather sensor
    # create a default class SmartObject for the weather sensor cluster 
    weather = sensors.create({'resourceName': 'rhvWeather-01', 'resourceClass': 'SmartObject'}) 
                        
    # example description in simple link-format like concepts
    baseObject.Description.set((URIRef('sensors/rhvWeather-01'), Literal('resourceClass'), Literal('SmartObject')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01'), Literal('resourceType'), Literal('SensorSystem')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01'), Literal('sensorType'), Literal('Weather')))
    #
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/outdoor_temperature'), Literal('interfaceType'), Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/outdoor_temperature'), Literal('resourceType'), Literal('temperature')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/outdoor_humidity'), Literal('interfaceType'), Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/outdoor_humidity'), Literal('resourceType'), Literal('humidity')))
      
    
    # now create an Observable Property for each sensor output
    pushInterval = 10 # number of samples to delay each push to Xively

    outdoor_temperature = weather.create({'resourceName': 'outdoor_temperature',\
                                          'resourceClass': 'ObservableProperty'})
    
    outdoor_temperature.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com',\
                                        'pubTopic': ''})
     
    outdoor_humidity = weather.create({'resourceName': 'outdoor_humidity',\
                                        'resourceClass': 'ObservableProperty'})
        
    outdoor_humidity.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com',\
                                        'pubTopic': ''})
     
      
    try:
    # register handlers etc.
        while 1: sleep(1)
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'

    