#!/bin/env python3
# -*- coding: utf-8 -*-
'''
Утиліта для полегшення імпорта данних
Written by Andriy Danyleiko and Liudmyla Kislitsyna
Send bugs to andrii.danyleiko@gmail.com
'''

import math
import sys
import urllib

import fastkml
import overpy


def get_pass_from_overpass(longitude_west, latitude_south, longitude_east, latitude_north): #Задаєм стандартний BBOX
    # південна_широта, західна_довгота, північна_широта, східна_довгота
    '''
    get pass from OSM database thru overpass API from bounding box.
    Bbox formats:
    bbox = left,bottom,right,top
    bbox = min Longitude , min Latitude , max Longitude , max Latitude
    
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
    result = api.query(_query_pattern.format(latitude_south,longitude_west,latitude_north,longitude_east))
    passes = []
    for i in result.nodes:
        passes.append(i.tags)
    return passes


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


def point_inside_polygon(x,y,poly):
    '''determine if a point is inside a given polygon or not
    Polygon is a list of (x,y) pairs.'''
    n = len(poly)
    inside =False
    
    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y
    
    return inside


def poly2bbox(poly):
    '''обчислюємо крайні точки полігона'''
    lats = [point[1] for point in poly]
    lons = [point[0] for point in poly]
    
    longitude_west = min(lons) #долгота левой границы 
    longitude_east = max(lons) #долгота правой границы
    latitude_north = max(lats) #широта верхней границы
    latitude_south = min(lats) #широта нижней границы
    
    return round(longitude_west,6), round(latitude_south,6), round(longitude_east,6), round(latitude_north,6)


def get_pass_westra(longitude_west, latitude_south, longitude_east, latitude_north):
    '''Функція для витягування геопривязаних перевалів із Вестри в kml xml формат.
    poly will be converted to bbox'''
    url = 'http://westra.ru/passes/kml/passes.php'
    values = {'BBOX' : '{0},{1},{2},{3}'.format(longitude_west, latitude_south, longitude_east, latitude_north)}
    #data = urllib.urlencode(values)
    r_url = url + '?BBOX=' + values['BBOX']
    response = urllib.urlopen(r_url)
    if response.getcode() != 200:
        print 'westra.ru return not 200 HTTP code'
        sys.exit(100)
    k = fastkml.kml.KML()
    k.from_string(response.read())
    features = list(k.features())
    if len(features) == 1:
        features = features[0]
    else:
        raise NotImplementedError('There are more than 1 feature in object')
    ff = list(features.features())
    placemarks = []
    for folder in ff:
        if isinstance(folder,fastkml.kml.Folder):
            for p in folder.features():
                placemarks.append(p)
        else:
            raise NotImplementedError('There are not fastkml.kml.Folder object in list')
    
    
    #req = urllib2.Request(url, data)
    #response = urllib2.urlopen(req)
    #the_page = response.read()
    return placemarks


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True, report=True) #raise_on_error=True
