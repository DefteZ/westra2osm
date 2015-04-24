#!/bin/env python
# -*- coding: utf-8 -*-
'''
Утиліта для полегшення імпорта данних
Written by Andriy Danyleiko and Liudmyla Kislitsyna
Send bugs to andrii.danyleiko@gmail.com
'''

import math

def distance_between_points(lat1, lon1, lat2, lon2):
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)
    delta_lat = math.fabs(lat2 - lat1)
    delta_lon = math.fabs(lon2 - lon1)
    return math.sqrt(delta_lat ** 2 + delta_lon ** 2)
