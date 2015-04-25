#!/bin/env python3
# -*- coding: utf-8 -*-
'''
Утиліта для полегшення імпорта данних
Written by Andriy Danyleiko and Liudmyla Kislitsyna
Send bugs to andrii.danyleiko@gmail.com
'''

import math
import sys

import overpy


def get_pass_from_overpass(bbox):
    '''
    descriptions
    example get_pass_from_overpass((42.79741601927622,76.61865234374999,43.24520272203359,77.81341552734375))
    '''
    _query_pattern = '''[out:json][timeout:25];
(
  node["mountain_pass"="yes"]({},{},{},{});
);
out body;
>;
out skel qt;'''
    api = overpy.Overpass()
    result = api.query(_query_pattern.format(*bbox))
    for i in result.nodes:
        print ('назва: {};'.format(i.tags['name']))


def distance_between_points(lat1, lon1, lat2, lon2):
    '''
    функція для пошуку відстані між точками у градусах
    TODO: зробить у метрах
    
    >>> distance_between_points(1, 1, 1, 2)
    1.0
    >>> distance_between_points(1, 1, 1, 1)
    0.0
    >>> distance_between_points(2,5,6,7) - 4.47213595499958 < sys.float_info.epsilon
    True
    '''
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)
    delta_lat = math.fabs(lat2 - lat1)
    delta_lon = math.fabs(lon2 - lon1)
    return math.sqrt(delta_lat ** 2 + delta_lon ** 2)


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True, report=True) #raise_on_error=True
