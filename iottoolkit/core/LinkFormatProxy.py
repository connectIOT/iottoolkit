'''
Created on Sep 21, 2013

LinkFormatProxy provides a Core Link-Format interface to a SmartObject Description. 
The Link-Format Interface provides a subset of the relations found in the description
based on bindings of Link-Format attributes to RDF Predicates

This is meant to expose an object at .well-known/core in the object hierarchy where
.well-known is a nested smart object and core is an instance of this proxy

The CoAP server maps POST to the set operation and PUT to the create operation
The HTTP server maps PUT to the set operation and POST to the create operation

core-link-format examples:

<subject1>;predicate="object";predicate="object",<sublect2>...

<sensors/rhvWeather-01/outdoor_humidity>;rt="humidity";if="sensor",
<sensors/rhvWeather-01/daily_rain>;rt="depth";if="sensor"

multiple objects are separated by whitespace
<subject1>;predicate="object1 object2 object3"
</leds/top/right>;color="red orange yellow green blue white"

@author: mjkoster
'''

from RESTfulResource import RESTfulResource
from rdflib.graph import Graph
from rdflib.term import Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, OWL
from Observers import Observers

 
class LinkFormatProxy (RESTfulResource):
    
    def __init__(self, parentObject=None, resourceName=''):
        RESTfulResource.__init__(self, parentObject, resourceName)
        # make a reference to the graph inside the associated Description resource
        self.graph = self.resources['parentObject'].resources['parentObject'].Description.graph
        # This resource supports link-format only
        self._parseContentTypes = [ 'application/link-format' ]
        self._serializeContentTypes = [ 'application/link-format' ]
        self.fmt = { 'application/link-format': 'linkFormat' }
        
        # attribute - predicate bindings RDF - core-link-format
        self._attrToPred = {'rt': Literal('resourceType'),
                            'if': Literal('interfaceType') }
        
        self._predToAttr = {Literal('resourceType'): 'rt',
                            Literal('interfaceType') : 'if' }


    def get(self, query=None):
        # return a sub-graph consisting of the triples with predicates in the attribute binding
        # filtered by the query 
        g = Graph()        
        if query == None:
            for self._pred in self._predToAttr:
                for triple in self.graph.triples((None, self._pred, None)) :
                    g.add(triple)
        else:
            self._attr, self._obj = query.split('=')
            for (self._subject, p, o) in self.graph.triples( (None, self._attrToPred[self._attr], Literal(self._obj)) ) :
                # return all links for all attributes in the binding that have matching subjects
                for self._pred in self._predToAttr:
                    for triple in self.graph.triples((self._subject, self._pred, None)) :
                        g.add(triple)          
        return g
    
    def set(self, newGraph):
        # update description graph with new subgraph
        for self._triple in newGraph.triples((None,None,None)):
            self.graph.add(self._triple)
        
    # exposed methods for converting sub graphs to and from specified representation
    def parse(self, source, cType):
        # assume format = link-format
        g = Graph()
        self._linkFormatString = source
        self._graphs = self._linkFormatString.split(',')
        for self._graph in self._graphs:
            self._links = self._graph.split(';')
            self._subject = self._links[0]
            self._subject = self._subject.strip('<')
            self._subject = self._subject.strip('>')
            for self._link in self._links[1:]:
                self._attr, self._objs = self._link.split('=')
                self._objs = self._objs.strip('"') # remove quotes from object string
                self._objs = self._objs.split(' ')
                for self._obj in self._objs:
                    g.add( ( URIRef(self._subject), self._attrToPred[self._attr], Literal(self._obj) ) )            
        return g 
    
    def serialize(self, graph, cType):
        # assume format = link-format
        self._subjects = [] # triple store returns a triple for each s,p.o so need to filter unique subjects
        self._subjStrings = [] # accumulate a list of subject strings + link-format relation + value strings
        for self._subj in graph.subjects(None, None):
            if self._subj not in self._subjects:
                self._subjects.append(self._subj) # list of unique subjects to filter duplicates
                self._subjString = '<' + str(self._subj) + '>'
                for self._pred in graph.predicates(self._subj, None):
                    self._subjString += ';' + self._predToAttr[self._pred] + '='
                    self._objs = []
                    for self._obj in graph.objects(self._subj, self._pred):
                        self._objs.append(self._obj)
                    self._subjString += '"' + ' '.join(self._objs) + '"'
                self._subjStrings.append(self._subjString)
        return str(','.join(self._subjStrings)) # collapse the list down to a string
       
    def serializeContentTypes(self) :
        return self._serializeContentTypes
    
    def parseContentTypes(self) :
        return self._parseContentTypes
    
        