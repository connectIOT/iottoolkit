#!/usr/bin/env python
#
# HYPERCAT.PY
# Copyright (c) 2013 Pilgrim Beart <firstname.lastname@1248.io>
# 
# Enables easy creation of valid Hypercat catalogues
# Written to comply with IoT Ecosystems Demonstrator Interoperability Action Plan V1.0 24th June 2013
# As found at http://www.openiot.org/apis
#
##Permission is hereby granted, free of charge, to any person obtaining a copy
##of this software and associated documentation files (the "Software"), to deal
##in the Software without restriction, including without limitation the rights
##to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
##copies of the Software, and to permit persons to whom the Software is
##furnished to do so, subject to the following conditions:
##
##The above copyright notice and this permission notice shall be included in
##all copies or substantial portions of the Software.
##
##THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
##IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
##FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
##AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
##LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
##OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
##THE SOFTWARE.
##
## Usage:
##    Create a hypercat object
##    Optionally, add metadata to it with .addRelation()
##    Optionally, add items to the catalogue with .addItem()
##        (an item is either a hypercat or a resource)
##    Output it as JSON, either minimally or prettyprinted
##
## Example:
##    # Create a catalogue
##    h = Hypercat("CatalogueContainingOneCatalogueAndOneResource")
##    # Create a second catalogue, and add it as a child of the first
##    h2 = Hypercat("ChildCatalogue")
##    h.addItem(h2, "http://FIXMEcat")
##    # Create a resource, and add it as another child of the first catalogue
##    r = resource("resource1", "application/vnd.tsbiot.sensordata+json")
##    h.addItem(r, "http://FIXMEresource")
##    # Print the raw JSON of the catalogue, and then with human-friendly formatting
##    print h.asJSON()
##    print h.prettyprint()
##
## See unit tests for more examples

# TODO:
#   4.3.3 Says that it is optional to use isContentType to tag each member of items[]
#   However we treat it here as mandatory.
#
#
# HOW IT WORKS
# According to the spec, each Catalogue has a (human-readable) description and a list of metadata about it.
# It also contains a list of "items", and each item has an HREF and a list of metadata about it.
# An item can be any kind of resource, including another catalogue.
#
# So conceptually, catalogues can have many levels of hierarchy (i.e. a catalogue can contain a catalogue which contains a catalogue and so on).
# (Catalogues don't just have to be trees either, they can be graphs, contain loops etc.)
# And clients of this module will often want to declare full catalogue structures several levels deep, i.e. build their entire hierarchy in one go.
#
# But according to the 1.0 spec only one level of Catalogue can be output at a time,
# i.e. getting a catalogue will declare its child catalogues, but not its grand-children
# (to see the grand-children, you'd have to get the child catalogue)
#
# A further complication is some asymmetry in how attributes are declared
# when a catalogue is the parent, vs. when it is the child
#
# To deal with this, within this module we maintain a universal base class for every hypercat object.
# Then during output, we ignore grand-children, and modify attributes as necessary.
 
import json

REL = "rel"
VAL = "val"

# Catalogue structure
CATALOGUE_METADATA  = "item-metadata"    # Name of the array of metadata about the catalogue itself
ITEMS = "items"
HREF = "href"
ITEM_METADATA = "i-object-metadata" # Name of the array of metadata about each item in the catalogue

# Mandatory relations & types
ISCONTENTTYPE_RELATION = "urn:X-tsbiot:rels:isContentType"  # Mandatory for catalogues, but not resources
CATALOGUE_TYPE = "application/vnd.tsbiot.catalogue+json"
DESCRIPTION_RELATION = "urn:X-tsbiot:rels:hasDescription:en"

# Optional relations & types
SUPPORTS_SEARCH_RELATION = "urn:X-tsbiot:rels:supportsSearch"
SUPPORTS_SEARCH_VAL = "urn:X-tsbiot:search:simple"
HAS_HOMEPAGE_RELATION = "urn:X-tsbiot:rels:hasHomepage"
CONTAINS_CONTENT_TYPE_RELATION = "urn:X-tsbiot:rels:containsContentType"

# We manage Catalogues and Resources as raw Python JSON objects (i.e. we construct them in their final form)

def _values(metadata, rel):
    """Searches a set <metadata> to find all relations <rel>
    Returns a list of the values of those relations
    (A list, because a rel can occur more than once)"""
    result = []
    for r in metadata:
        if(r[REL] == rel):
            result.append(r[VAL])

    return result

class Base:
    # Functionality common to both Catalogues and Resources
    def __init__(self):
        self.metadata = []  # Called either CATALOGUE_METADATA or RESOURCE_METADATA
        self.items = []     # Only for Catalogues. Held as list of instances.
        self.href = None    # Only for Resources

    def addRelation(self, rel, val):
        self.metadata += [{REL:rel, VAL:val}]

    def replaceRelation(self, rel, val):
        for i in range(len(self.metadata)):
            if self.metadata[i][REL]==rel:
                self.metadata[i][REL]=val

    def rels(self):
        """Returns a LIST of all the metadata relations"""
        r = []
        for i in self.metadata:
            r = r + i[REL]
        return []
        
    def values(self, rel):
        """Returns a LIST of the values of all relations of type rel, since HyperCat allows rels to be repeated"""
        return _values(self.metadata, rel)
    
    def prettyprint(self):
        """Return hypercat formatted prettily"""
        return json.dumps(self.asJSON(), sort_keys=True, indent=4, separators=(',', ': '))

    def asJSONstr(self):
        """Return hypercat as a string, of minimum length"""
        return json.dumps(self.asJSON(), sort_keys=True, separators=(',', ':'))

    def isCatalogue(self):
        return CATALOGUE_TYPE in self.values(ISCONTENTTYPE_RELATION)

    def setHref(self,href):
        self.href=href
        
class Hypercat(Base):
    """Create a valid Hypercat catalogue"""
    # Catalogues must be of type catalogue, have a description, and contain at least an empty array of items

    def __init__(self, description):
        Base.__init__(self)
        assert isinstance(description, basestring), "Description argument must be a string"
        # TODO: Check description is ASCII, since JSON can only encode that
        self.metadata = [
            { REL:ISCONTENTTYPE_RELATION, VAL:CATALOGUE_TYPE },
            { REL:DESCRIPTION_RELATION, VAL:description }]

    def asJSON(self, asChild=False):
        j = {}
        if(asChild):
            j[HREF] = self.href
            j[ITEM_METADATA] = self.metadata
        else:
            j[CATALOGUE_METADATA] = self.metadata
            j[ITEMS]=[]
            for c in self.items:
                j[ITEMS] += [c.asJSON(asChild=True)]
        return j

    def addItem(self, child, href):
        """Add a new item (a catalogue or resource) as a child of this catalogue."""
        assert isinstance(child, Base), "child must be a hypercat Catalogue or Resource"
        child.setHref(href)
        for item in self.items:
            assert item.href != href, "All items in a catalogue must have unique hrefs : "+href
        self.items += [child]           # Add new
        return        

    def replaceItem(self, child, href):
        """Replace an existing child (by matching the href). Guarantees not to change the order of items[]"""
        assert isinstance(child, Base), "child item must be a hypercat Catalogue or Resource"
        for i in range(len(self.items)):
            if(self.items[i].href == href):
                self.items[i] = child   # Replace existing
                return
        assert False, "No such child item to replace as "+href

    def description(self):  # 1.0 spec is unclear about whether there can be more than one description. We assume not.
        return self.values(DESCRIPTION_RELATION)[0]

    def items(self):
        return self.items
    
    def supportsSimpleSearch(self):
        self.addRelation(SUPPORTS_SEARCH_RELATION, SUPPORTS_SEARCH_VAL)

    def hasHomepage(self, url):
        self.addRelation(HAS_HOMEPAGE_RELATION, url)

    def containsContentType(self, contentType):
        self.addRelation(CONTAINS_CONTENT_TYPE_RELATION, contentType)

    def findByPath(self, rel, path):
        """Traverses children, building a path based on relation <rel>, until given path is found."""
        if((path=="") or (path=="/")):
            return(self)
        (front,dummy,rest) = path.lstrip("/").partition("/")
        for child in self.items:
            if front in child.values(rel):
                return child.findByPath(rel, rest)
        return None

    def recurse(self, fn, *args):
        """Calls fn on a hypercat and all its child hypercats (not resources)"""
        fn(self, *args)
        for i in self.items:
            if isinstance(i, Hypercat):
                self.recurse(i, *args)
        
class Resource(Base):
    """Create a valid Hypercat Resource"""
    # Resources must have an href, have a declared type, and have a description
    def __init__(self, description, contentType):
        """contentType must be a string containing an RFC2046 MIME type"""
        Base.__init__(self)
        self.metadata = [
            {REL:ISCONTENTTYPE_RELATION,VAL:contentType},
            {REL:DESCRIPTION_RELATION,VAL:description}]

    def asJSON(self, asChild=True):
        # Resources can only be children
        j = {}
        j[ITEM_METADATA] = self.metadata
        j[HREF] = self.href
        return j
    
def loads(inputStr):
    """Takes a string and converts it into an internal hypercat object, with some checking"""
    inCat = json.loads(inputStr)
    assert CATALOGUE_TYPE in _values(inCat[CATALOGUE_METADATA], ISCONTENTTYPE_RELATION)
    # Manually copy mandatory fields, to check that they are they, and exclude other garbage
    desc = _values(inCat[CATALOGUE_METADATA], DESCRIPTION_RELATION)[0]  # TODO: We are ASSUMING just one description, which may not be true
    outCat = Hypercat(desc)
    for i in inCat[ITEMS]:
        href = i[HREF]
        contentType = _values(i[ITEM_METADATA], ISCONTENTTYPE_RELATION) [0]
        desc = _values(i[ITEM_METADATA], DESCRIPTION_RELATION) [0]
        if contentType == CATALOGUE_TYPE:
            r = Hypercat(desc)
        else:
            r = Resource(desc, contentType)
        outCat.addItem(r, href)

    return outCat

#if __name__ == '__main__':
    # Unit tests
    #import unittest
    #unittest.unittest()
