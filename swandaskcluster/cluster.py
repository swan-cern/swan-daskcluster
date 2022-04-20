
from . import config
from .utils import SchedulerConfig

from dask_lxplus import CernCluster

import dask


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
        self._scheduler_config = SchedulerConfig()
        private_hostname = self._scheduler_config.get_private_hostname()
        contact_hostname = self._scheduler_config.get_contact_hostname()

        try:
            port = self._scheduler_config.get_port()

            scheduler_options['host']            = f'{private_hostname}:{port}'
            scheduler_options['contact_address'] = f'{contact_hostname}:{port}'

            super().__init__(worker_image = worker_image,
                             job_extra = { **config_job_extra, **job_extra },
                             scheduler_options = scheduler_options,
                             **base_class_kwargs)
        except Exception:
            # Something went wrong.
            # Release the port so that it can be given to other processes and
            # re-raise
            self._scheduler_config.release_port()
            raise

        # The scheduler was successfully created, we can keep the port
        self._scheduler_config.reserve_port()
