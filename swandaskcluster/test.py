import socket
from pathlib import Path
from cluster import SwanHTCondorCluster
from distributed import Client

def inc(x):
    return x + 1


with SwanHTCondorCluster(
) as cluster:
    print("PRINTING JOB SCRIPT")
    print(cluster.job_script())
    with Client(cluster) as client:
        cluster.scale(1)
        futures = []
        for i in range(10):
            f = client.submit(inc, 10)
            futures.append(f)
        print('Result is {}'.format(client.gather(futures)))