
from . import config
from .utils import DaskSchedulerConfig, NoPortsException, GeneralException

from dask_lxplus import CernCluster
from dask_lxplus.cluster import CernJob

import dask
from distributed.security import Security

import os, logging

# Logging
log = logging.getLogger('swan-daskcluster')

# TLS files
CA_CERT = 'ca.crt'
SERVER_CERT = 'server.crt'
SERVER_KEY = 'server.key'


class SwanDaskClusterException(Exception):
    '''
    Generic class for exceptions occurred when creating Dask clusters from SWAN.
    '''
    pass


class SwanHTCondorJob(CernJob):
    '''
    Class that modifies the HTCondor job arguments so that the TLS certificates
    can be found on the cluster side by the Dask worker. For that purpose, we
    construct a new Security argument that does not include the absolute path
    on the client side where those certificates are stored -- that path won't
    exist in the workers.
    '''

    def __init__(self, *args, **kwargs):
        # Discard the general Security object and construct a new one just for
        # the workers
        # Make sure files are specified relative to the working directory on
        # the cluster side (HTCondor sandbox)
        kwargs['security'] = Security(
                                tls_ca_file = CA_CERT,
                                tls_worker_cert = SERVER_CERT,
                                tls_worker_key = SERVER_KEY)

        super().__init__(*args, **kwargs)


class SwanHTCondorCluster(CernCluster):
    '''
    Class that configures an HTCondorCluster to be used from SWAN.
    '''

    config_name = 'swan'
    job_cls = SwanHTCondorJob

    def __init__(self,
                 job_extra = {},
                 scheduler_options = {},
                 **base_class_kwargs):
        '''
        Configures the Dask workers to be used by SWAN clients and dynamically
        obtains the necessary addresses for a Dask scheduler that runs in a
        SWAN user session.
        '''

        # Worker configuration
        worker_image = dask.config.get(
                           f'jobqueue.{self.config_name}.worker-image')
        tag = os.getenv('VERSION_DOCKER_IMAGE', None)
        if tag is None:
            raise SwanDaskClusterException(
                'Error when creating a SwanHTCondorCluster: could not '
                'find the tag to be used for the worker image')
        worker_image += f':{tag}'

        config_job_extra = dask.config.get(
                               f'jobqueue.{self.config_name}.job-extra')

        # TODO: set a value for 'log_directory'

        # Security
        security = self.security()
        if security is None:
            raise SwanDaskClusterException(
                'Error when creating a SwanHTCondorCluster: could not '
                'configure TLS')
        tls_job_extra = self._get_tls_job_extra(security)
        protocol = 'tls'

        # Scheduler configuration
        self._scheduler_config = DaskSchedulerConfig()
        try:
            port = self._scheduler_config.get_port()
        except NoPortsException as npe:
            raise SwanDaskClusterException(
                'Error when creating a SwanHTCondorCluster: no more clusters '
                'can be created due to the lack of free ports. Please remove '
                'one of the existing clusters before creating a new one') \
            from npe
        except GeneralException as ge:
            raise SwanDaskClusterException(
                'Error when creating a SwanHTCondorCluster: an unknown error '
                'occurred when trying to obtain a port for the new cluster') \
            from ge

        private_hostname = self._scheduler_config.get_private_hostname()
        contact_hostname = self._scheduler_config.get_contact_hostname()

        scheduler_options['protocol']        = protocol
        scheduler_options['host']            = f'{private_hostname}:{port}'
        scheduler_options['contact_address'] = f'{protocol}://{contact_hostname}:{port}'

        try:
            super().__init__(worker_image = worker_image,
                             job_extra = { **config_job_extra,
                                           **job_extra,
                                           **tls_job_extra },
                             scheduler_options = scheduler_options,
                             security = security,
                             protocol = f'{protocol}://',
                             **base_class_kwargs)
        except Exception as e:
            # Some exception was raised in any of the cluster superclasses.
            # Release the port so that it can be given to other processes and
            # re-raise from the original exception.
            self._scheduler_config.release_port()
            raise SwanDaskClusterException(
                'Error when creating a SwanHTCondorCluster') from e

        # The scheduler was successfully created, we can keep the port
        self._scheduler_config.reserve_port()

    @classmethod
    def security(cls):
        '''
        Constructs and returns a Dask Security object if a directory with
        pregenerated certificates is found. Otherwise it logs an error and
        returns None.
        The certificates should have been generated during user session
        startup, if the user selected to work with an HTCondor cluster.
        Client, scheduler and workers share the same certificate, signed by the
        same CA.
        '''

        dask_tls_dir = os.environ.get('DASK_TLS_DIR', None)

        if dask_tls_dir is None:
            log.error('No Dask TLS directory is configured')
            return None

        ca_cert = f'{dask_tls_dir}/{CA_CERT}'
        server_cert = f'{dask_tls_dir}/{SERVER_CERT}'
        server_key = f'{dask_tls_dir}/{SERVER_KEY}'

        for f in ca_cert, server_cert, server_key:
            if not os.path.isfile(f):
                log.error(f'Cannot find {f} for TLS configuration')
                return None

        return Security(
            tls_ca_file=ca_cert,
            tls_worker_cert=server_cert,
            tls_worker_key=server_key,
            tls_client_cert=server_cert,
            tls_client_key=server_key,
            tls_scheduler_cert=server_cert,
            tls_scheduler_key=server_key,
            require_encryption=True,
        )

    def _get_tls_job_extra(self, security):
        '''
        Returns a dictionary with some extra configuration options for an
        HTCondor job related to TLS. Such options enable the (encrypted)
        transfer of the CA certificate as well as the certificate and key to be
        used by Dask workers.
        '''

        config = security.get_tls_config_for_role('worker')
        tls_files = f'{config["ca_file"]}, {config["cert"]}, {config["key"]}'

        return { 'transfer_input_files': tls_files,
                 'encrypt_input_files': tls_files,
                 'should_transfer_files': 'YES' }