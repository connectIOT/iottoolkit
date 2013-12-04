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
from time import sleep
import sys


if __name__ == '__main__' :
    
    baseObject = HttpObjectService().baseObject # make an instance of the service, default object root and default port 8000
    print 'httpd started at', baseObject.Properties.get('httpService')

    # create the weather station resource template
    # first the description 
    baseObject.Description.set((URIRef('sensors/rhvWeather-01'), RDFS.Class, Literal('SmartObject')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01'), RDFS.Resource, Literal('SensorSystem')))
    baseObject.Description.set((URIRef('sensors/rhvWeather-01'), RDF.type, Literal('WeatherSensor')))
    
    # sensors resource under the baseObject for all sensors    
    sensors = baseObject.create({'resourceName': 'sensors',\
                                 'resourceClass': 'SmartObject'}) # top level object container for sensors, default class is SmartObject
    #weather resource under sensors for the weather sensor    
    weather = sensors.create({'resourceName': 'rhvWeather-01', \
                             'resourceClass': 'SmartObject'}) # create a default class SmartObject for the weather sensor cluster

    # make a reference to the weather sensor object Description and build an example graph (could use the built-in reference as well)
    weather.description = weather.Resources.get('Description')
    weather.description.set((URIRef('sensors/rhvWeather-01/outdoor_temperature'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/outdoor_temperature'), RDF.type, Literal('temperature')))
    weather.description.set((URIRef('sensors/rhvWeather-01/outdoor_humidity'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/outdoor_humidity'), RDF.type, Literal('humidity')))
    weather.description.set((URIRef('sensors/rhvWeather-01/sealevel_pressure'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/sealevel_pressure'), RDF.type, Literal('pressure')))
    weather.description.set((URIRef('sensors/rhvWeather-01/indoor_temperature'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/indoor_temperature'), RDF.type, Literal('temperature')))
    weather.description.set((URIRef('sensors/rhvWeather-01/indoor_humidity'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/indoor_humidity'), RDF.type, Literal('humidity')))
    weather.description.set((URIRef('sensors/rhvWeather-01/wind_gust'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/wind_gust'), RDF.type, Literal('speed')))
    weather.description.set((URIRef('sensors/rhvWeather-01/wind_speed'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/wind_speed'), RDF.type, Literal('speed')))
    weather.description.set((URIRef('sensors/rhvWeather-01/wind_direction'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/wind_direction'), RDF.type, Literal('direction')))
    weather.description.set((URIRef('sensors/rhvWeather-01/current_rain'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/current_rain'), RDF.type, Literal('depth')))
    weather.description.set((URIRef('sensors/rhvWeather-01/hourly_rain'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/hourly_rain'), RDF.type, Literal('depth')))
    weather.description.set((URIRef('sensors/rhvWeather-01/daily_rain'), RDFS.Resource, Literal('sensor')))
    weather.description.set((URIRef('sensors/rhvWeather-01/daily_rain'), RDF.type, Literal('depth')))
    
    # now create an Observable Property for each sensor output

    outdoor_temperature = weather.create({'resourceName': 'outdoor_temperature',\
                                          'resourceClass': 'ObservableProperty'})
    
    outdoor_humidity = weather.create({'resourceName': 'outdoor_humidity',\
                                        'resourceClass': 'ObservableProperty'})
        
    sealevel_pressure = weather.create({'resourceName': 'sealevel_pressure',\
                                        'resourceClass': 'ObservableProperty'})
    
    indoor_temperature = weather.create({'resourceName': 'indoor_temperature',\
                                          'resourceClass': 'ObservableProperty'})

    indoor_humidity = weather.create({'resourceName': 'indoor_humidity',\
                                        'resourceClass': 'ObservableProperty'})
    
    wind_gust = weather.create({'resourceName': 'wind_gust',\
                                'resourceClass': 'ObservableProperty'})
    
    wind_speed = weather.create({'resourceName': 'wind_speed',\
                                  'resourceClass': 'ObservableProperty'})
        
    wind_direction = weather.create({'resourceName': 'wind_direction',\
                                    'resourceClass': 'ObservableProperty'})
    
    current_rain = weather.create({'resourceName': 'current_rain',\
                                    'resourceClass': 'ObservableProperty'})
    
    hourly_rain = weather.create({'resourceName': 'hourly_rain',\
                                  'resourceClass': 'ObservableProperty'})
    
    daily_rain = weather.create({'resourceName': 'daily_rain',\
                                 'resourceClass': 'ObservableProperty'})
 
    # note that by default, a publisher and a subscriber are created with topic = object path
    sealevel_pressure.Observers.create({'resourceName': 'mqttTestObserver',\
                                        'resourceClass': 'mqttObserver',\
                                        'connection': 'smartobjectservice.com',\
                                        'QoS': 0,\
                                        'keepAlive': 60 })
    
    # the observer publishes on the sealevel_pressure topic, which is subscribed to by that OP ;-)
    outdoor_temperature.Observers.create({'resourceName': 'mqttTestObserver',\
                                          'resourceClass': 'mqttObserver',\
                                          'connection': 'smartobjectservice.com',\
                                          'pubTopic': '/sensors/rhvWeather-01/sealevel_pressure',\
                                          'subTopic': None,\
                                          'QoS': 0,\
                                          'keepAlive': 60 })

    outdoor_humidity.Observers.create({'resourceName': 'mqttTestObserver',\
                                          'resourceClass': 'mqttObserver',\
                                          'connection': 'smartobjectservice.com',\
                                          'pubTopic': None,\
                                          'subTopic': '/sensors/rhvWeather-01/sealevel_pressure',\
                                          'QoS': 0,\
                                          'keepAlive': 60 })
    
    
    try:
    # register handlers etc.
        while 1: sleep(1)
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'

    