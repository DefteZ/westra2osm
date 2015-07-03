#!/bin/env python
# -*- coding: utf-8 -*-
import sys, argparse, codecs
reload(sys)
sys.setdefaultencoding('utf-8')
#another way sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

#import lxml.html

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
    
    bbox = poly2bbox(poly)
    
    westra_kml_passes = get_pass_westra(*bbox)
    osm_passes = get_pass_from_overpass(*bbox)
    
    d_passes = {}
    
    for p in westra_kml_passes:
        if p.name.startwith(u'вер. '):
            continue
        name = p.name.lstrip(u'пер. ')
        if name in d_passes:
            d_passes[name][0] = name
        else:
            d_passes[name] = [name, u'']
    
    for p in osm_passes:
        name = p[u'name']
        if name in d_passes:
            d_passes[name][1] = name
        else:
            d_passes[name] = [u'', name]
    if cli_args.file:
        f = codecs.open(cli_args.file, "w", encoding="utf-8")
    else:
        f = sys.stdout
    
    #write header
    f.write (u'''<!DOCTYPE HTML>
<html>
<title>OSM валідатор перевалів</title>
<meta charset="utf-8">
<meta name="keywords" content="Вестра, OSM, Openstreetmap, westra, kml"> 
<body><table border>
<tr><th>Перевал в каталогі "Вестри"</th><th>Перевал в ОСМ</th></tr>''')
    for i in d_passes.values():
        f.write(u'''        <tr><td>{0!s}</td><td>{1!s}</td></tr>\n'''.format(*i))
    
    #write footer
    f.write('    </table>\n    </body>\n    </html>')
    

def createParser():
    '''create cli options'''
    myFormater = lambda prog: argparse.RawDescriptionHelpFormatter(prog,max_help_position=25,width=190)
    parser = argparse.ArgumentParser(formatter_class=myFormater)
    parser.add_argument('-p', '--poly', help='Polygon of area that will be used for validation. Point should be splited by spaces. Format "lat1,lon1 lat2,lon2 ...".  Example "14.01,10.1 15,10.5 14.5,12.7"')
    #TODO
    parser.add_argument('-f', '--file', help='File what html will be saved')
    #output file format
    #polyfile
    return parser


main()