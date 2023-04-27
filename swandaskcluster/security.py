from .cluster import SwanHTCondorCluster

def loader(info):
    '''
    Implements a default security loader for Dask clients. When a Dask Client
    object is created, this function will be called and will provide the
    client with a Security object, which is obtained from SwanHTCondorCluster.
    Note how the security configuration that the Dask client obtains is the
    same as the one used by the Dask scheduler.

    To tell Dask to use this function, the following variable is set in the
    notebook and terminal environments:
    DASK_DISTRIBUTED__CLIENT__SECURITY_LOADER="swandaskcluster.security.loader"
    '''

    return SwanHTCondorCluster.security()
