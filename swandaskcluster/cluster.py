
from . import config
from .utils import DaskSchedulerConfig, NoPortsException, GeneralException

from dask_lxplus import CernCluster

import dask


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
                 worker_image = None,
                 job_extra = {},
                 scheduler_options = {},
                 **base_class_kwargs):
        '''
        Configures the Dask workers to be used by SWAN clients and dynamically
        obtains the necessary addresses for a Dask scheduler that runs in a
        SWAN user session.
        '''

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

        scheduler_options['host']            = f'{private_hostname}:{port}'
        scheduler_options['contact_address'] = f'{contact_hostname}:{port}'

        try:
            super().__init__(worker_image = worker_image,
                             job_extra = { **config_job_extra, **job_extra },
                             scheduler_options = scheduler_options,
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
