'''
Created on July 26, 2013

Example service created for a weather sensor. An Arduino POSTs simple JSON value-only updates to the
REST endpoints defined by the Observable Property created for each sensor output. An example graph is 
created to demonstrate how endpoints can be discovered by reading the graph meta data

@author: mjkoster
'''
from SmartObject.SmartObject import SmartObject
from SmartObject.Description import Description
from SmartObject.ObservableProperty import ObservableProperty
from SmartObject.Observers import Observers
from SmartObject.PropertyOfInterest import PropertyOfInterest
from rdflib.term import Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, OWL
from ObjectService.HttpObjectService import HttpObjectService
from ObjectService.CoapObjectService import CoapObjectService
from time import sleep
import sys


if __name__ == '__main__' :
    
    baseObject = HttpObjectService().baseObject # make an instance of the service, default object root and default port 8000
    print 'httpd started at', baseObject.Properties.get('httpService')
    
    coapService = CoapObjectService(baseObject)

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
    baseObject.Description.set((URIRef('sensors/rhvWeather-01'), RDFS.Class, Literal('SmartObject')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01'), RDF.type, Literal('SensorSystem')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01'), RDFS.Resource, Literal('Weather')))
    #
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/outdoor_temperature'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/outdoor_temperature'), RDFS.Resource, Literal('temperature')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/outdoor_humidity'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/outdoor_humidity'), RDFS.Resource, Literal('humidity')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/sealevel_pressure'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/sealevel_pressure'), RDFS.Resource, Literal('pressure')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/indoor_temperature'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/indoor_temperature'), RDFS.Resource, Literal('temperature')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/indoor_humidity'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/indoor_humidity'), RDFS.Resource, Literal('humidity')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/wind_gust'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/wind_gust'), RDFS.Resource, Literal('speed')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/wind_speed'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/wind_speed'), RDFS.Resource, Literal('speed')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/wind_direction'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/wind_direction'), RDFS.Resource, Literal('direction')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/current_rain'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/current_rain'), RDFS.Resource, Literal('depth')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/hourly_rain'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/hourly_rain'), RDFS.Resource, Literal('depth')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/daily_rain'), RDF.type, Literal('sensor')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01/daily_rain'), RDFS.Resource, Literal('depth')))
    
    
    # now create an Observable Property for each sensor output
    pushInterval = 10 # number of samples to delay each push to Xively

    outdoor_temperature = weather.create({'resourceName': 'outdoor_temperature',\
                                          'resourceClass': 'ObservableProperty'})
    
    outdoor_temperature.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
    outdoor_humidity = weather.create({'resourceName': 'outdoor_humidity',\
                                        'resourceClass': 'ObservableProperty'})
        
    outdoor_humidity.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
    sealevel_pressure = weather.create({'resourceName': 'sealevel_pressure',\
                                        'resourceClass': 'ObservableProperty'})
    
    sealevel_pressure.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
    indoor_temperature = weather.create({'resourceName': 'indoor_temperature',\
                                          'resourceClass': 'ObservableProperty'})

    indoor_temperature.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
    indoor_humidity = weather.create({'resourceName': 'indoor_humidity',\
                                        'resourceClass': 'ObservableProperty'})
    
    indoor_humidity.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
    wind_gust = weather.create({'resourceName': 'wind_gust',\
                                'resourceClass': 'ObservableProperty'})
    
    wind_gust.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
    wind_speed = weather.create({'resourceName': 'wind_speed',\
                                  'resourceClass': 'ObservableProperty'})
        
    wind_speed.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
    wind_direction = weather.create({'resourceName': 'wind_direction',\
                                    'resourceClass': 'ObservableProperty'})
    
    wind_direction.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
    current_rain = weather.create({'resourceName': 'current_rain',\
                                    'resourceClass': 'ObservableProperty'})
    
    current_rain.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
    hourly_rain = weather.create({'resourceName': 'hourly_rain',\
                                  'resourceClass': 'ObservableProperty'})
    
    hourly_rain.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
    daily_rain = weather.create({'resourceName': 'daily_rain',\
                                 'resourceClass': 'ObservableProperty'})
 
    daily_rain.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com'})
     
      
    try:
    # register handlers etc.
        while 1: sleep(1)
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'

    