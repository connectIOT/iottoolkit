'''
Created on Dec 7, 2013

Minimal service creation, base object auto-created by the first server, 
passed to constructor of second server 

@author: mjkoster
'''
from interfaces.HttpObjectService import HttpObjectService
from interfaces.CoapObjectService import CoapObjectService
from time import sleep

if __name__ == '__main__' :
    
    # make an empty instance of a SmartObject shared by 2 interfaces, 
    # CoAP and HTTP, default object root and default ports 5683 and 8000
    # CoAP service makes the base object and it is passed to the http service constructor
    HttpObjectService( CoapObjectService().baseObject ) 
          
    try:
    # register handlers etc.
        while 1: sleep(1)
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'

    