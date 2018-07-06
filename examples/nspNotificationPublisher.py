'''
Created 11/3/2014 MJ Koster

Create a resource to receive NSP Notification channel pushes and publish them to an MQTT topic

'''
from InstanceConstructor import SystemInstance
from time import sleep

systemConstructor = {
'service_metadata': {
    'FQDN': '',
    'IPV4': '',
    'IPV6': ''
    },
#replace with unique service URIs e.g. http://localhost:8000  when starting service instances
'services': {
    'localHTTP' : {
        'scheme': 'http',
        'FQDN': 'localhost',
        'port': 8000,
        'IPV4': '',
        'root': '/',
        'discovery': '/'
                    },                
             },

'object_metadata': {
    'objectPath': '',
    },

'objects': {
    '/': {
        'resourceName': '/',
        'resourceClass': 'SmartObject'
        },
    '/services': {
        'resourceName': 'services',
        'resourceClass': 'SmartObject'
        },
    '/nspEvents': {
        'resourceName': 'nspEvents',
        'resourceClass': 'ObservableProperty',
        'publishesTo': ['mqtt://smartobjectservice.com:1883/nspEvents']
        }
    }
}


if __name__ == '__main__' :
    '''
    make an IoT Toolkit instance using the system constructor
    '''
    system = SystemInstance(systemConstructor)
    
    try:
    # register handlers etc.
        while 1: sleep(1)
    except KeyboardInterrupt: pass
    print 'got KeyboardInterrupt'

