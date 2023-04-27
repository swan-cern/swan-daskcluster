# SWAN Dask Cluster

Package to create wrappers of Dask clusters to be used from SWAN.

## Requirements

* dask_lxplus
* swanportallocator

## Install

```bash
pip install swandaskcluster
```

## Security

This package provides a
[security loader](https://docs.dask.org/en/stable/configuration.html#distributed.client.security-loader)
function to automatically set the appropriate TLS configuration in Dask clients
created from SWAN.

This makes it possible to create Dask clients in the following way:

```python
from dask.distributed import Client

client = Client("tls://10.100.244.186:30124")
```

i.e. with no need to construct and pass a `Security` object as part of the
`Client` constructor.
