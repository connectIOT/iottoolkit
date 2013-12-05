'''
Created on Sep 15, 2012

Observers class for observation of changes in a resource

Updated July 28, 2013 MJK - made a simple http ObserverPublisher prototype
Updated Aug 17, 2013 MJK - implemented new Observers-Observer pattern using config settings from dict(JSON)

To use the observer, create an observer subclass resource endpoint using http POST or the Python API

the observer subclass httpPublisher updates the endpoint at the specified URL with a JSON object 
representing the value of the Observable Property whenever the Observable Property is updated

other observer subclasses are httpSubscriber, which creates a remote httpPublisher, 
and handlerNotifier, which invokes the handleNotify method of handler

It doesn't call notify if you try to directly update the Property Of Interest, POI needs to call onUpdate also

An Observer is created subordinate to the Observers resource, and configured with a particular observer 
class using a PUT (set) of a JSON (dictionary) settings object

@author: mjkoster
'''
from RESTfulResource import RESTfulResource
from urlparse import urlparse
import json
import httplib
import mosquitto # should try and catch exception if mosquitto not installed    


class Observer(RESTfulResource):
    def __init__(self, parentObject=None, resourceDescriptor = {}):
        RESTfulResource.__init__(self, parentObject, resourceDescriptor)
        self._settings = self._resourceDescriptor
        self._baseObject = self.resources['baseObject']
        self._linkBaseDict = self.resources['baseObject'].resources
        self._thisURI =  self.resources['baseObject'].Properties.get('httpService') \
                    + self.resources['parentObject'].resources['parentObject'].Properties.get('pathFromBase')
        self._settings.update({'thisURI': self._thisURI})
        self._init() 
        
    def _init(self):
        pass

    def _updateSettings(self):
        pass

    def get(self, Key=None):
        if Key != None :
            return self._settings[Key]
        else :
            return self._settings
        
    def set(self, newSettings):
        self._settings.update(newSettings) 
        self._updateSettings() # to synchronize the state of other resources in derived classes     
        
    def notify(self, resource):
        self._notify(resource)
        
    def _notify(self, resource):
        pass

    def linkToRef(self, linkPath ):
        '''
        takes a path string and walks the object tree from a base dictionary
        returns a ref to the resource at the path endpoint
        '''
        self._currentDict = self._linkBaseDict
        self._pathElements = linkPath.split('/')
        for pathElement in self._pathElements[:-1] : # all but the last, which should be the endpoint
            if len(pathElement) > 0 : # first element is a zero length string for some reason
                self._currentDict = self._currentDict[pathElement].resources
        self._resource = self._currentDict[self._pathElements[-1] ]
        return self._resource        


class httpPublisher(Observer):
    def _notify(self,resource): # JSON only for now
        self._jsonObject = json.dumps(resource.get())
        self._uriObject = urlparse(self._settings['targetURI'])
        self._httpConnection = httplib.HTTPConnection(self._uriObject.netloc)
        self._httpConnection.request('PUT', self._uriObject.path, self._jsonObject, {"Content-Type" : "application/json" })
        self._httpConnection.getresponse()
        return


class callbackNotifier(Observer):    
    def _notify(self,resource=None): # invoke the handler
        self.linkToRef(urlparse(self._settings['handlerURI']).path).handleNotify(resource)
        return
    

class httpSubscriber(Observer):
    # wait until settings are updated using the SET operation 
    def _init(self):
        self._observerSettings = {}
        if 'observerURI' in self._settings: # means Subscriber settings were passed in on constructor
            self._createRemoteObserver()
            
    def _updateSettings(self):
        if self._settings.has_key('observerURI'): # if the observerURI is in the subscriber settings
            if not 'observerURI' in self._observerSettings : # but not in the remote observer settings
                self._createRemoteObserver() # then make the remote Observer
         
    def _createRemoteObserver(self):
        # this creates the remote observer instance. 
        self._thisURI = self._settings['thisURI']
        
        self._observerURI = self._settings['observerURI']
        self._observerName = self._settings['observerName']
        
        self._observerDescriptor = {'resourceName': self._observerName,\
                                    'resourceClass': 'httpPublisher' }
        self._observerSettings = {'targetURI': self._thisURI}
        # build and send the requests to create the remote Observer
        self._jsonHeader = {"Content-Type" : "application/json" }        
        self._uriObject = urlparse(self._observerURI)
        self._httpConnection = httplib.HTTPConnection(self._uriObject.netloc)
        # create the named resource for the Observer
        self._httpConnection.request('POST', self._uriObject.path + '/Observers', \
                                     json.dumps(self._observerDescriptor), self._jsonHeader)
        self._httpConnection.getresponse()
        # configure the Observer
        self._httpConnection.request('PUT', self._uriObject.path + '/Observers' + '/' + self._observerName, \
                                     json.dumps(self._observerSettings), self._jsonHeader)
        self._httpConnection.getresponse()
        return
    
    
class xivelyPublisher(Observer):
    def _init(self):
        self._apiPath = self._settings['apiBase'] + '/' + self._settings['feedID'] + '.json'        
        self._uriObject = urlparse(self._apiPath)
        self._requestHeader = {'Content-Type': 'application/json', 'X-ApiKey': self._settings['apiKey'] }        
        self._streamBody = {'id': self._settings['streamID'], 'current_value': 0 }    
        self._requestBody = {'version': '1.0.0', 'datastreams': [ self._streamBody ] }
        if 'updateInterval' in self._settings:
            self._updateInterval = self._settings['updateInterval']
        else:
            self._updateInterval = 1
        self._nextUpdateDelay = 1 # always send the first update, then count down from Interval
        
    def _notify(self, resource=None):
        self._nextUpdateDelay -= 1
        if not self._nextUpdateDelay:
            self._nextUpdateDelay = self._updateInterval
            self._streamBody.update({'current_value': resource.get() })
            self._httpConnection = httplib.HTTPConnection(self._uriObject.netloc)
            self._httpConnection.request('PUT', self._uriObject.path, json.dumps(self._requestBody), self._requestHeader )
            self._httpConnection.getresponse()
  
  
class mqttObserver(Observer):
    # mqttObserver creates a subscriber and publisher using the same connection
    # this enables it to act as an agent to mirror the REST resource
    # a filter prevents updates from being recursively applied
    def _init(self):
        # read and check settings and set defaults
        if not 'connection' in self._settings :
            self._settings.update({'connection': 'localhost'})            
        self._connection = self._settings['connection']        
        if ':' in self._connection :
            self._host, self._port = self._connection.split(':')
            self._port = int(self._port)
        else:
            self._host = self._connection
            self._port = 1883        
            
        # parent of the Observers container is the ObservableProperty                 
        self._objectPath = \
        self.resources['parentObject'].resources['parentObject'].Properties.get('pathFromBase') 
        self._observableProperty = self.resources['parentObject'].resources['parentObject']  
        
        # default settings to pub and sub, 60 second keepalive, QoS=0
        if not 'subTopic' in self._settings: 
            self._settings.update({'subTopic': self._objectPath})
        self._subTopic = self._settings['subTopic']
        
        if not 'pubTopic' in self._settings:
            self._settings.update({'pubTopic': self._objectPath})        
        self._pubTopic = self._settings['pubTopic']        
        
        if not 'keepAlive' in self._settings:
            self._settings.update({'keepAlive': 60 })
        self._keepAlive = self._settings['keepAlive']    
                
        if not 'QoS' in self._settings:
            self._settings.update({'QoS': 0})
        self._QoS = self._settings['QoS']
        
        # the state machine
        self._pubs = {} # outstanding topics for filter kludge, prevents cycle due to re-applying REST update
        self._connected = False
        self._subscribed = False
        self._waitConnack = False
        self._waitSuback = False
        self._waitPuback = False
        self._updating = False
                
        def on_connect(mosq, obj, rc):
            print("connected: rc: "+str(rc))
            self._waitConnack = False
            self._connected = True

        def on_message(mosq, obj, msg):
            print("message: " + msg.topic +" "+str(msg.qos)+" "+str(msg.payload))
            if self._subTopic not in self._pubs : # filter to stop cycle can cause lost MQTT update
                self._updating = True
                # update the Observable Property assuming it's a JSON for now...
                self._observableProperty.set(json.loads(msg.payload))
                self._updating = False
            else :
                self._pubs.pop(self._subTopic) # remove the entry

        def on_publish(mosq, obj, mid):
            print("puback: mid: "+str(mid))
            self._waitPuback = False

        def on_subscribe(mosq, obj, mid, granted_qos):
            print("suback: mid, qos:"+str(mid)+" "+str(granted_qos))
            self._waitSuback = False
            self._subscribed = True

        def on_log(mosq, obj, level, string):
            print(string)

        # make a client instance, assign handlers, and startup
        self._mqttc = mosquitto.Mosquitto()
        self._mqttc.on_message = on_message
        self._mqttc.on_connect = on_connect
        self._mqttc.on_publish = on_publish
        self._mqttc.on_subscribe = on_subscribe
        # Uncomment to enable debug messages
        # self._mqttc.on_log = on_log
        
        # start a daemon thread to run the interface
        self._mqttc.loop_start() 
        
        # open the connection
        self._waitConnack = True
        self._mqttc.connect(self._host, self._port, self._keepAlive)
        while self._waitConnack : pass
        
        # start the subscription from the broker if any
        if not self._subTopic == '':
            self._waitSuback = True
            self._mqttc.subscribe(self._subTopic, self._QoS)
            while self._waitSuback : pass
                        
    def _notify(self, resource):
        if not self._pubTopic == '' : # if there is a topic to publish
            # we don't want to republish the same update in progress recursively
            if not (self._updating and (self._pubTopic == self._subTopic)): 
                if self._pubTopic == self._subTopic : # update the one-shot kludge filter if there is a potential cycle
                    self._pubs.update({self._pubTopic: None}) 
                self._waitPuback = True
                self._mqttc.publish(self._pubTopic, json.dumps(resource.get()), self._QoS )
                while self._waitPuback : pass


class coapNotifier(Observer):
    # created when a CoAP GET with Observe option is accepted
    # when notified of a resource update, sends a CoAP response packet to the client
    def _init(self):
        self._client = None
        self._token = None
        self._seqNo = None
        self._maxAge = None
        pass
    
    def _notify(self, resource):
        # send a 200 response to the client
        pass
    
    def delete(self):
        # send 400 response and remove resources
        pass


class Observers(RESTfulResource): 
    # the Observers resource is a container for individual named Observer resources, created for each Observable Property resource
    def __init__(self, parentObject=None, resourceDescriptor = {}):
        RESTfulResource.__init__(self, parentObject, resourceDescriptor)
        self._observers = {}
               
    def onUpdate(self,resource):
        self._onUpdate(resource)
        
    def _onUpdate(self, resource):
        for observer in self._observers :
            self._observers[observer].notify(resource)

    def get(self, Key=None):
        if Key == None :
            return self._observers.keys() # if no URI specified then return all observers
        return self._observer[Key] #return a handle to the observer object for python API
    
    # map the set operation to the create operation
    def set(self):
        pass
    
    # new create takes dictionary built from JSON object POSTed to parent resource
    def create(self, resourceDescriptor):
        resourceName = resourceDescriptor['resourceName']
        resourceClass = resourceDescriptor['resourceClass']
        if resourceName not in self.resources:
            # create new instance of the named class and add to resources directory, return the ref
            self.resources.update({resourceName : globals()[resourceClass](self, resourceDescriptor)}) 
            self._observers.update({resourceName: self.resources[resourceName]})            
        return self.resources[resourceName] # returns a reference to the created instance

    # delete removes an observer from the list, echoes None for failure
    def delete(self, observerName):
        if observerName in self._observers.keys() :
            self._observers.remove(observerName)
            self.resources.remove(observerName)
            return observerName
        return None
    
    