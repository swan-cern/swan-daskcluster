from .cluster import SwanHTCondorCluster

def loader(info):
    return SwanHTCondorCluster.security()
