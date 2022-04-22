
import os

from swanportallocator.portallocator import PortAllocatorClient, NoPortsException, GeneralException


class DaskSchedulerConfig:
    '''
    Helper class that provides information that is relevant for a Dask
    scheduler running in a SWAN user session, namely:
    - Private hostname: hostname that resolves to a private address that
    belongs to Docker's bridge network. The scheduler binds to such address.
    - Contact hostname: the hostname of the server that hosts the container.
    Used by the workers to contact the scheduler.
    - Port: a `PortAllocatorClient` is created to reserve a port for the
    scheduler to listen on, since it needs to receive connections from the
    workers.
    '''

    def __init__(self):
        '''
        Initializes a client of the SwanPortAllocator extension.
        '''
        self._port_allocator = PortAllocatorClient()
        self._port_allocator.connect()

    def get_private_hostname(self):
        '''
        Returns the local hostname of the SWAN user session, to which the
        scheduler will bind.
        '''
        return os.environ['HOSTNAME']

    def get_contact_hostname(self):
        '''
        Returns the name of the host that runs the SWAN user session container,
        which will be used by the workers to contact the scheduler.
        '''
        return os.environ['SERVER_HOSTNAME']

    def get_port(self):
        '''
        Requests and returns a free port for the scheduler to use.
        '''
        return self._port_allocator.get_ports(1)[0]

    def reserve_port(self):
        '''
        Reserves a previously requested port.
        '''
        self._port_allocator.set_connected()

    def release_port(self):
        '''
        Releases a previously requested port.
        '''
        self._port_allocator.set_disconnected()
