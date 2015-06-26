#!/bin/env python
# -*- coding: utf-8 -*-
import sys, argparse

import lxml.html

import westra2osm_lib
from westra2osm_lib import *

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
    bbox = poly2bbox(poly)
    
    westra_kml_passes = get_pass_westra(*bbox)
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


def calculete_tiles():
    raise NotImplementedError

import math
def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)


def get_pass_overpass():
    raise NotImplementedError




'''
class Pass():
    raise NotImplementedError
    self.ks
    self.name
'''



main()
