'''
CoapObjectService creates a CoAP service endpoint at the specified port, based on the object pointer
passed into the constructor
'''
import socket
import struct
import logging
import threading
import json

from socket import gethostname, getfqdn


class CoapObjectService(object):
    def __init__(self, baseObject=None, port=None): # FIXME if no baseObject given, create a default base object

        if port == None:
            self._port = 5683 # IETF default port for coap://
        else:
            self._port = port
            
        if baseObject == None:
            from SmartObject.SmartObject import SmartObject
            self._baseObject = SmartObject()
        else:
            self._baseObject = baseObject
            
        self.resources = self._baseObject.resources
                
        self._host = gethostname()
        self._baseObject.Properties.update({'coapService': 'coap://' + self._host + ':' + repr(self._port)})

        self._coapHandler = CoapRequestHandler(self._baseObject)
        self._coapServer = COAPServer(self._host, self._port, self._coapHandler) 
        print 'CoAP Service started at', baseObject.Properties.get('coapService')
        #starts thread as daemon, has run method loop
        
    @property    
    def baseObject(self):
        return self._baseObject


class CoapRequestHandler(object):
    def __init__(self,baseObject):
        self._linkCache = {}
        self._linkBaseDict = baseObject.resources
    
    def do_GET(self, path, options=None):
        self._query = None
        self._observing = False
        for option in options:
            (number, value) = option.values()
            if number == COAPOption.URI_QUERY:
                self._query = value
            if number == COAPOption.OBSERVE:
                self._observing = True
        self._currentResource = self.linkToRef(path)
        
        if hasattr(self._currentResource, 'serialize'):
            self._contentType = self._currentResource._serializeContentTypes[0]
            return 200, self._currentResource.serialize(self._currentResource.get(self._query), self._contentType), self._contentType
        else:
            self._contentType='application/json'
            return 200, json.dumps(self._currentResource.get()), self._contentType
    
    def do_POST(self, path, payload, options=None):
        self._currentResource = self.linkToRef(path)
        if hasattr(self._currentResource, 'serialize'):
            self._contentType=self._currentResource._serializeContentTypes[0]
            self._currentResource.set( self._currentResource.parse(str(payload), self._contentType) )
            return 200, '', self._contentType     
        else:    
            self._contentType='application/json'
            self._currentResource.set(json.loads(str(payload)))
            return 200, '', self._contentType
    
    def do_PUT(self, path, payload, flag):
        pass
    
    def do_DELETE(self, path, payload, flag):
        pass
    
    def linkToRef(self, linkPath):
        '''
        takes a path string and walks the object tree from a base dictionary
        returns a ref to the resource at the path endpoint
        store translations in a hash cache for fast lookup after the first walk
        '''
        self._linkPath = linkPath
        if self._linkPath in self._linkCache.keys() :
            return self._linkCache[self._linkPath]
        # cache miss, walk path and update cache at end
        self._currentDict = self._linkBaseDict
        self._pathElements = linkPath.split('/')
        for pathElement in self._pathElements[:-1] : # all but the last, which should be the endpoint
            self._currentDict = self._currentDict[pathElement].resources
        self._resource = self._currentDict[self._pathElements[-1] ]
        #self._linkCache.update({ self._linkPath : self._resource })
        return self._resource
        
    def getByLink(self, linkPath):
        return self.linkToRef(linkPath).get()

    def setByLink(self, linkPath, newValue):
        self.linkToRef(linkPath).set(newValue)

#
# coap.py
#
#   Copyright 2012-2013 Eric Ptak - trouch.com
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
'''
added options passed to handler, added Observe (6) to options 
'''
#from webiopi.utils.version import PYTHON_MAJOR
PYTHON_MAJOR=2
#from webiopi.utils.logger import info, exception 
def info(msg):
    print(msg)

def exception(e):
    raise(e)
'''
import socket
import struct
import logging
import threading
'''
M_PLAIN = "text/plain"
M_JSON  = "application/json"

if PYTHON_MAJOR >= 3:
    pass #from urllib.parse import urlparse
else:
    from urlparse import urlparse

#try :
#    import _webiopi.GPIO as GPIO
#except:
#    pass
GPIO=None

def HTTPCode2CoAPCode(code):
    return int(code/100) * 32 + (code%100)

   
class COAPContentFormat():
    FORMATS = {0: "text/plain",
               40: "application/link-format",
               41: "application/xml",
               42: "application/octet-stream",
               47: "application/exi",
               50: "application/json"
               }

    @staticmethod
    def getCode(fmt):
        if fmt == None:
            return None
        for code in COAPContentFormat.FORMATS:
            if COAPContentFormat.FORMATS[code] == fmt:
                return code
        return None
    
    @staticmethod
    def toString(code):
        if code == None:
            return None

        if code in COAPContentFormat.FORMATS:
            return COAPContentFormat.FORMATS[code]
        
        raise Exception("Unknown content format %d" % code)
        

class COAPOption():
    OPTIONS = {1: "If-Match",
               3: "Uri-Host",
               4: "ETag",
               5: "If-None-Match",
               6: "Observe",
               7: "Uri-Port",
               8: "Location-Path",
               11: "Uri-Path",
               12: "Content-Format",
               14: "Max-Age",
               15: "Uri-Query",
               16: "Accept",
               20: "Location-Query",
               35: "Proxy-Uri",
               39: "Proxy-Scheme"
               }
    
    IF_MATCH = 1
    URI_HOST = 3
    ETAG = 4
    IF_NONE_MATCH = 5
    OBSERVE=6
    URI_PORT = 7
    LOCATION_PATH = 8
    URI_PATH = 11
    CONTENT_FORMAT = 12
    MAX_AGE = 14
    URI_QUERY = 15
    ACCEPT = 16
    LOCATION_QUERY = 20
    PROXY_URI = 35
    PROXY_SCHEME = 39
    
    
class COAPMessage():
    TYPES = ["CON", "NON", "ACK", "RST"]
    CON = 0
    NON = 1
    ACK = 2
    RST = 3

    def __init__(self, msg_type=0, code=0, uri=None):
        self.version = 1
        self.type    = msg_type
        self.code    = code
        self.id      = 0
        self.token   = None
        self.options = []
        self.host    = ""
        self.port    = 5683
        self.uri_path = ""
        self.content_format = None
        self.payload = None
        
        if uri != None:
            p = urlparse(uri)
            self.host = p.hostname
            if p.port:
                self.port = int(p.port)
            self.uri_path = p.path
        
    def __getOptionHeader__(self, byte):
        delta  = (byte & 0xF0) >> 4
        length = byte & 0x0F
        return (delta, length)  
        
    def __str__(self):
        result = []
        result.append("Version: %s" % self.version)
        result.append("Type: %s" % self.TYPES[self.type])
        result.append("Code: %s" % self.CODES[self.code])
        result.append("Id: %s" % self.id)
        result.append("Token: %s" % self.token)
        #result.append("Options: %s" % len(self.options))
        #for option in self.options:
        #    result.append("+ %d: %s" % (option["number"], option["value"]))
        result.append("Uri-Path: %s" % self.uri_path)
        result.append("Content-Format: %s" % (COAPContentFormat.toString(self.content_format) if self.content_format else M_PLAIN))
        result.append("Payload: %s" % self.payload)
        result.append("")
        return '\n'.join(result)
        
    def getOptionHeaderValue(self, value):
        if value > 268:
            return 14
        if value > 12:
            return 13
        return value
    
    def getOptionHeaderExtension(self, value):
        buff = bytearray()
        v = self.getOptionHeaderValue(value)
        
        if v == 14:
            value -= 269
            buff.append((value & 0xFF00) >> 8)
            buff.append(value & 0x00FF)

        elif v == 13:
            value -= 13
            buff.append(value)

        return buff
    
    def appendOption(self, buff, lastnumber, option, data):
        delta = option - lastnumber
        length = len(data)
        
        d = self.getOptionHeaderValue(delta)
        l = self.getOptionHeaderValue(length)
        
        b  = 0
        b |= (d << 4) & 0xF0  
        b |= l & 0x0F
        buff.append(b)
        
        ext = self.getOptionHeaderExtension(delta);
        for b in ext:
            buff.append(b)

        ext = self.getOptionHeaderExtension(length);
        for b in ext:
            buff.append(b)

        for b in data:
            buff.append(b)

        return option

    def getBytes(self):
        buff = bytearray()
        byte  = (self.version & 0x03) << 6
        byte |= (self.type & 0x03) << 4
        if self.token:
            token_len = min(len(self.token), 8);
        else:
            token_len = 0
        byte |= token_len
        buff.append(byte)
        buff.append(self.code)
        buff.append((self.id & 0xFF00) >> 8)
        buff.append(self.id & 0x00FF)
        
        if self.token:
            for c in self.token:
                buff.append(c)

        lastnumber = 0
        
        if len(self.uri_path) > 0:
            paths = self.uri_path.split("/")
            for p in paths:
                if len(p) > 0:
                    if PYTHON_MAJOR >= 3:
                        data = p.encode()
                    else:
                        data = bytearray(p)
                    lastnumber = self.appendOption(buff, lastnumber, COAPOption.URI_PATH, data)

        if self.content_format != None:
            data = bytearray()
            fmt_code = self.content_format
            if fmt_code > 0xFF:
                data.append((fmt_code & 0xFF00) >> 8)
            data.append(fmt_code & 0x00FF)
            lastnumber = self.appendOption(buff, lastnumber, COAPOption.CONTENT_FORMAT, data)
            
        buff.append(0xFF)
        
        if self.payload:
            if PYTHON_MAJOR >= 3:
                data = self.payload.encode()
            else:
                data = bytearray(self.payload)
            for c in data:
                buff.append(c)
        
        return buff
    
    def parseByteArray(self, buff):
        self.version = (buff[0] & 0xC0) >> 6
        self.type    = (buff[0] & 0x30) >> 4
        token_length = buff[0] & 0x0F
        index = 4
        if token_length > 0:
            self.token = buff[index:index+token_length]

        index += token_length
        self.code    = buff[1]
        self.id      = (buff[2] << 8) | buff[3]
        
        number = 0

        # process options
        while index < len(buff) and buff[index] != 0xFF:
            (delta, length) = self.__getOptionHeader__(buff[index])
            offset = 1

            # delta extended with 1 byte
            if delta == 13:
                delta += buff[index+offset]
                offset += 1
            # delta extended with 2 buff
            elif delta == 14:
                delta += 255 + ((buff[index+offset] << 8) | buff[index+offset+1])
                offset += 2
            
            # length extended with 1 byte
            if length == 13:
                length += buff[index+offset]
                offset += 1
                
            # length extended with 2 buff
            elif length == 14:
                length += 255 + ((buff[index+offset] << 8) | buff[index+offset+1])
                offset += 2

            number += delta
            valueBytes = buff[index+offset:index+offset+length]
            # opaque option value
            if number in [COAPOption.IF_MATCH, COAPOption.ETAG]:
                value = valueBytes
            # integer option value
            elif number in [COAPOption.URI_PORT, COAPOption.CONTENT_FORMAT, COAPOption.MAX_AGE, COAPOption.ACCEPT]:
                value = 0
                for b in valueBytes:
                    value <<= 8
                    value |= b
            # string option value
            else:
                if PYTHON_MAJOR >= 3:
                    value = valueBytes.decode()
                else:
                    value = str(valueBytes)
            self.options.append({'number': number, 'value': value})
            index += offset + length

        index += 1 # skip 0xFF / end-of-options
        
        if len(buff) > index:
            self.payload = buff[index:]
        else:
            self.payload = ""
        
        for option in self.options:
            (number, value) = option.values()
            if number == COAPOption.URI_PATH:
                self.uri_path += "/%s" % value
 

class COAPRequest(COAPMessage):
    CODES = {0: None,
             1: "GET",
             2: "POST",
             3: "PUT",
             4: "DELETE"
             }

    GET    = 1
    POST   = 2
    PUT    = 3
    DELETE = 4

    def __init__(self, msg_type=0, code=0, uri=None):
        COAPMessage.__init__(self, msg_type, code, uri)

class COAPGet(COAPRequest):
    def __init__(self, uri):
        COAPRequest.__init__(self, COAPMessage.CON, COAPRequest.GET, uri)

class COAPPost(COAPRequest):
    def __init__(self, uri):
        COAPRequest.__init__(self, COAPMessage.CON, COAPRequest.POST, uri)

class COAPPut(COAPRequest):
    def __init__(self, uri):
        COAPRequest.__init__(self, COAPMessage.CON, COAPRequest.PUT, uri)

class COAPDelete(COAPRequest):
    def __init__(self, uri):
        COAPRequest.__init__(self, COAPMessage.CON, COAPRequest.DELETE, uri)

class COAPResponse(COAPMessage):    
    CODES = {0: None,
             64: "2.00 OK",
             65: "2.01 Created",
             66: "2.02 Deleted",
             67: "2.03 Valid",
             68: "2.04 Changed",
             69: "2.05 Content",
             128: "4.00 Bad Request",
             129: "4.01 Unauthorized",
             130: "4.02 Bad Option",
             131: "4.03 Forbidden",
             132: "4.04 Not Found",
             133: "4.05 Method Not Allowed",
             134: "4.06 Not Acceptable",
             140: "4.12 Precondition Failed",
             141: "4.13 Request Entity Too Large",
             143: "4.15 Unsupported Content-Format",
             160: "5.00 Internal Server Error",
             161: "5.01 Not Implemented",
             162: "5.02 Bad Gateway",
             163: "5.03 Service Unavailable",
             164: "5.04 Gateway Timeout",
             165: "5.05 Proxying Not Supported"            
            }

    # 2.XX
    OK      = 64
    CREATED = 65
    DELETED = 66
    VALID   = 67
    CHANGED = 68
    CONTENT = 69
    
    # 4.XX
    BAD_REQUEST         = 128
    UNAUTHORIZED        = 129
    BAD_OPTION          = 130
    FORBIDDEN           = 131
    NOT_FOUND           = 132
    NOT_ALLOWED         = 133
    NOT_ACCEPTABLE      = 134
    PRECONDITION_FAILED = 140
    ENTITY_TOO_LARGE    = 141
    UNSUPPORTED_CONTENT = 143
    
    # 5.XX
    INTERNAL_ERROR          = 160
    NOT_IMPLEMENTED         = 161
    BAD_GATEWAY             = 162
    SERVICE_UNAVAILABLE     = 163
    GATEWAY_TIMEOUT         = 164
    PROXYING_NOT_SUPPORTED  = 165
    
    def __init__(self):
        COAPMessage.__init__(self)

class COAPClient():
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(1.0)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        
    def sendRequest(self, message):
        data = message.getBytes();
        sent = 0
        while sent<4:
            try:
                self.socket.sendto(data, (message.host, message.port))
                data = self.socket.recv(1500)
                response = COAPResponse()
                response.parseByteArray(bytearray(data))
                return response
            except socket.timeout:
                sent+=1
        return None

class COAPServer(threading.Thread):
    logger = logging.getLogger("CoAP")

    def __init__(self, host, port, handler):
        threading.Thread.__init__(self, name="COAPThread")
        self.handler = COAPHandler(handler)
        self.host = host
        self.port = port
        self.multicast_ip = '224.0.1.123'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', port))
        self.socket.settimeout(1)
        self.running = True
        self.daemon = True
        self.start()
        
    def run(self):
        info("CoAP Server at coap://%s:%s/" % (self.host, self.port))
        while self.running == True:
            try:
                (request, client) = self.socket.recvfrom(1500)
                requestBytes = bytearray(request)
                coapRequest = COAPRequest()
                coapRequest.parseByteArray(requestBytes)
                coapResponse = COAPResponse()
                #self.logger.debug("Received Request:\n%s" % coapRequest)
                self.processMessage(coapRequest, coapResponse)
                #self.logger.debug("Sending Response:\n%s" % coapResponse)
                responseBytes = coapResponse.getBytes()
                self.socket.sendto(responseBytes, client)
                self.logger.debug('"%s %s CoAP/%.1f" %s -' % (coapRequest.CODES[coapRequest.code], coapRequest.uri_path, coapRequest.version, coapResponse.CODES[coapResponse.code]))
                
            except socket.timeout as e:
                continue
            except Exception as e:
                if self.running == True:
                    exception(e)
            
        info("CoAP Server stopped")
    
    def enableMulticast(self):
        while not self.running:
            pass
        mreq = struct.pack("4sl", socket.inet_aton(self.multicast_ip), socket.INADDR_ANY)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        info("CoAP Server at coap://%s:%s/ (MULTICAST)" % (self.multicast_ip, self.port))
                
    def stop(self):
        self.running = False
        self.socket.close()
        
    def processMessage(self, request, response):
        if request.type == COAPMessage.CON:
            response.type = COAPMessage.ACK
        else:
            response.type = COAPMessage.NON

        if request.token:
            response.token = request.token

        response.id = request.id
        response.uri_path = request.uri_path
        
        if request.code == COAPRequest.GET:
            self.handler.do_GET(request, response)
        elif request.code == COAPRequest.POST:
            self.handler.do_POST(request, response)
        elif request.code / 32 == 0:
            response.code = COAPResponse.NOT_IMPLEMENTED
        else:
            exception(Exception("Received CoAP Response : %s" % response))
        
class COAPHandler():
    def __init__(self, handler):
        self.handler = handler
    
    def do_GET(self, request, response):
        try:
            (code, body, contentType) = self.handler.do_GET(request.uri_path[1:], request.options)
            if code == 0:
                response.code = COAPResponse.NOT_FOUND
            elif code == 200:
                response.code = COAPResponse.CONTENT
            else:
                response.code =  HTTPCode2CoAPCode(code)
            response.payload = body
            response.content_format = COAPContentFormat.getCode(contentType)
        #except (GPIO.InvalidDirectionException, GPIO.InvalidChannelException, GPIO.SetupException) as e:
            #response.code = COAPResponse.FORBIDDEN
            #response.payload = "%s" % e
        except Exception as e:
            response.code = COAPResponse.INTERNAL_ERROR
            raise e
        
    def do_POST(self, request, response):
        try:
            (code, body, contentType) = self.handler.do_POST(request.uri_path[1:], request.payload, request.options)
            if code == 0:
                response.code = COAPResponse.NOT_FOUND
            elif code == 200:
                response.code = COAPResponse.CHANGED
            else:
                response.code =  HTTPCode2CoAPCode(code)
            response.payload = body
            response.content_format = COAPContentFormat.getCode(contentType)
        #except (GPIO.InvalidDirectionException, GPIO.InvalidChannelException, GPIO.SetupException) as e:
            #response.code = COAPResponse.FORBIDDEN
            #response.payload = "%s" % e
        except Exception as e:
            response.code = COAPResponse.INTERNAL_ERROR
            raise e
        
