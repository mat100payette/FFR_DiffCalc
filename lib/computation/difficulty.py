import multiprocessing

from models import Chart

def compute_difficulties(charts: list[Chart]):
    '''Computes the difficulty of each `Chart` in `charts`.'''
    
    pool = multiprocessing.Pool()
    difficulties = pool.map(compute_difficulty, charts)

    return difficulties


def compute_difficulty(chart: Chart):
    '''Computes the difficulty of `chart`.'''
    return 1