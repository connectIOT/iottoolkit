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
    # print 'path = ', sys.path
    baseObject = SmartObject() # create a Smart Object to serve as the base container for other Smart Objects and resources
    server = HttpObjectService(baseObject) # make an instance of the service, baseObject is the object root
    server.start(8000) # forks a server thread to listen on port 8000
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
    
    pressure = weather.create({'resourceName': 'sealevel_pressure',\
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
 
    # test the simple http observer publisher 
    # make a named observer resource
    # configure the Observer to be an httpObserver and it's URI to PUT updates to
    # the publisher will use the scheme specified and update the URL endpoint whenever the OP is updated
    indoor_temperature.Observers.create({'resourceName': 'httpTempObserver',\
                                'resourceClass': 'httpPublisher',\
                                'targetURI': 'http://localhost:8000/sensors/rhvWeather-01/outdoor_temperature'})  

    # test the http Subscriber, which creates a remote observer at the location observerURI
    # make a named subscriber resource
    outdoor_humidity.Observers.create({'resourceName': 'humiditySubscriber',\
                                        'resourceClass': 'httpSubscriber',\
                                        'observerURI': 'http://localhost:8000/sensors/rhvWeather-01/indoor_humidity', \
                                        'observerName': 'humiditySubObserver' })

    # test the creation of handlers and invocation by Observers
   
    weather.Agent.create({'resourceName': 'logPrintHandler',\
                         'resourceClass': 'logPrintHandler'})
    
    indoor_temperature.Observers.create({'resourceName': 'tempPrintObserver',\
                                        'resourceClass': 'callbackNotifier',\
                                        'handlerURI': 'callback:///sensors/rhvWeather-01/Agent/logPrintHandler'})
    
    #addHandler class adds 2 properties values together and stores in a third
    weather.Agent.create({'resourceName': 'addHandler',\
                         'resourceClass': 'addHandler',\
                         'addendLink1':'sensors/rhvWeather-01/indoor_temperature', \
                         'addendLink2': 'sensors/rhvWeather-01/indoor_temperature', \
                         'sumOutLink': 'sensors/rhvWeather-01/outdoor_humidity'})
       
    # now create a callback observer endpoint 
    indoor_temperature.Observers.create({'resourceName': 'callbackTempObserver',\
                                         'resourceClass': 'callbackNotifier',\
                                         'handlerURI': 'callback:///sensors/rhvWeather-01/Agent/addHandler'})

     
    try:
    # register handlers etc.
        while 1: sleep(1)
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'

    