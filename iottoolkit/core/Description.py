'''
Created on Sep 15, 2012

Description class which is an instance of RDF graph from the rdflib Graph class
with consistent SmartObject interface methods. The parse and serialize methods 
work on the sub-graphs used by get and set methods for discovery and linkage

@author: mjkoster
'''

from RESTfulResource import RESTfulResource
from rdflib.graph import Graph
from Observers import Observers

class RespGraph(Graph):
    # add a method to convert to XML for RESTlite represent method
    def _xml_(self):
        return self.serialize(format='xml')
 
class Description (RESTfulResource):
    
    def __init__(self, parentObject=None, resourceName=''):
        RESTfulResource.__init__(self, parentObject, resourceName)
        self.graph = Graph()
        self._parseContentTypes = [ 'text/plain' , 'application/rdf+xml' , 'text/rdf+n3' ]
        self._serializeContentTypes = [ 'text/xml' , 'text/plain', 'application/rdf+xml' , 'application/x-turtle' , 'text/rdf+n3' ]
        self.fmt = { 'text/xml' : 'xml', 
               'application/rdf+xml' : 'xml',
               'application/x-turtle' : 'turtle',
               'text/rdf+n3' : 'n3',
               'text/plain' : 'nt'
               }
        

    # Description get method returns triples can be invoked via the 
    # property interface: SmartObject.Description  
    # Does the property decorator work for this?

    def get(self, (s,p,o) = (None,None,None)):
        # return a sub-graph consisting of the matching triples
        g = RespGraph()
        for triple in self.graph.triples((s,p,o)) :
            g.add(triple)
        return g
    
    # set existing triples (remove + add) 
    def set(self, newValue):
        if type(newValue) is tuple :
            self.graph.set(newValue)
        else :
            for triple in self.newValue.triples((None,None,None)):
                self.graph.add(triple)
    
    # add new triple or add new graph
    def create(self, newValue):    
        if type(newValue) is tuple :
            self.graph.add(newValue)
        else :
            self.graph += newValue
    
    # remove triple or remove sub-graph
    def delete(self, newValue):
        if type(newValue) is tuple :
            self.graph.remove(newValue)
        else :
            self.graph -= newValue
    
    # exposed methods for converting sub graphs 
    def parse(self,source, cType):
        g = Graph()
        return g.parse(source,format=self.fmt[cType])
    
    def serialize(self,graph, cType): 
        return graph.serialize(format=self.fmt[cType])
       
    def serializeContentTypes(self) :
        return self._serializeContentTypes
    
    def parseContentTypes(self) :
        return self._parseContentTypes
    
        