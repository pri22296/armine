from itertools import chain, combinations


def get_subsets(arr):
    return chain(*[combinations(arr, i+1) for i in range(len(arr))])
