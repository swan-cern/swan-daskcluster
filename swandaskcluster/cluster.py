from . import config
from .utils import DaskSchedulerConfig, NoPortsException, GeneralException

from dask_lxplus import CernCluster

import dask

import os
from pathlib import Path
from distributed.security import Security

SECRETS_DIR = Path("")
CA_FILE = SECRETS_DIR / "ca.pem"
CERT_FILE = SECRETS_DIR / "hostcert.pem"

class SwanDaskClusterException(Exception):
    '''
    Generic class for exceptions occurred when creating Dask clusters from SWAN.
    '''
    pass

class SwanHTCondorCluster(CernCluster):
    '''
    Class that configures an HTCondorCluster to be used from SWAN.
    '''

    config_name = 'swan'

    def __init__(self,
                 worker_image=None,
                 job_extra={},
                 security=None,
                 protocol=None,
                 scheduler_options={},
                 **base_class_kwargs
                 ):
        '''
        Configures the Dask workers to be used by SWAN clients and dynamically
        obtains the necessary addresses for a Dask scheduler that runs in a
        SWAN user session.
        '''
        #Security
        protocol = protocol or 'tls://'
        security = security or self.security()


        # Worker configuration

        worker_image = worker_image or \
                       dask.config.get(
                           f'jobqueue.{self.config_name}.worker-image')

        config_job_extra = dask.config.get(
            f'jobqueue.{self.config_name}.job-extra')

        # TODO: set a value for 'log_directory'

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


        scheduler_options['host'] = f'{private_hostname}:{port}'

        """
        still a mistery why the protocol needs to be set here
        """

        scheduler_options['contact_address'] = 'tls://'+f'{contact_hostname}:{port}'
        scheduler_options['protocol'] ='tls'

        try:
            super().__init__(worker_image=worker_image,
                             security=security,
                             protocol=protocol,
                             job_extra={**config_job_extra, **job_extra},
                             scheduler_options=scheduler_options,
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

    @staticmethod
    def check_and_generate_certificate():
        if os.path.exists(CA_FILE):
            print('certificate_exists')
        else:
            os.system(
                'openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout ' + str(CA_FILE) + ' -out ' + str(
                    CERT_FILE) + ' -subj "/C=US/ST=Utah/L=Lehi/O=Your Company, Inc./OU=IT/CN=yourdomain.com"')

    @classmethod
    def security(cls):
        """
        Return the Dask ``Security`` object
        """
        """
           Should we generate the certificate when the security is called? .
        """

        cls.check_and_generate_certificate()

        ca_file = str(CA_FILE)
        cert_file = str(CERT_FILE)
        return Security(
            tls_ca_file=ca_file,
            tls_worker_cert=cert_file,
            tls_worker_key=cert_file,
            tls_client_cert=cert_file,
            tls_client_key=cert_file,
            tls_scheduler_cert=cert_file,
            tls_scheduler_key=cert_file,
            require_encryption=True,
        )