#!/bin/env python
# -*- coding: utf-8 -*-
import sys, argparse
import urllib

import fastkml, lxml.html

import westra2osm_lib

def main():
    parser = createParser()
    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)
    cli_args = parser.parse_args()
    poly = []
    for point in cli_args.poly.split():
        coord = point.split(',')
        assert len(coord) == 2
        coord = tuple((float(coord[0]), float(coord[1])))
        poly.append(coord)
    else:
        poly = tuple(poly)
    
    print poly
    
    westra_kml_passes = get_pass_westra(poly)
    for p in westra_kml_passes:
        root = lxml.html.fromstring(p.description)
        rows = root.xpath("table")[0].findall("tr")
        ks = rows[2].getchildren()[1].text
        if ks and (u'1А' in ks or u'1Б' in ks or u'н/к' in ks):
            print p.name, ks


def createParser():
    '''create cli options'''
    myFormater = lambda prog: argparse.RawDescriptionHelpFormatter(prog,max_help_position=25,width=190)
    parser = argparse.ArgumentParser(formatter_class=myFormater)
    parser.add_argument('-p', '--poly', help='Polygon of area that will be used for validation. Point should be splited by spaces. Format "lat1,lon1 lat2,lon2 ...".  Example "14.01,10.1 15,10.5 14.5,12.7"')
    #TODO
    #output file
    #output file format
    #polyfile
    return parser


def poly2bbox(poly):
    '''обчислюємо крайні точки полігона'''
    lats = [point[1] for point in poly]
    lons = [point[0] for point in poly]
    
    longitude_west = min(lons) #долгота левой границы 
    longitude_east = max(lons) #долгота правой границы
    latitude_north = max(lats) #широта верхней границы
    latitude_south = min(lats) #широта нижней границы
    
    return round(longitude_west,6), round(latitude_south,6), round(longitude_east,6), round(latitude_north,6)


def calculete_tiles():
    raise NotImplementedError

import math
def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)


def get_pass_westra(poly):
    '''Функція для витягування геопривязаних перевалів із Вестри в kml xml формат.'''
    url = 'http://westra.ru/passes/kml/passes.php'
    values = {'BBOX' : '{0},{1},{2},{3}'.format(*poly2bbox(poly))}
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


def get_pass_overpass():
    raise NotImplementedError




'''
class Pass():
    raise NotImplementedError
    self.ks
    self.name
'''

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

main()
