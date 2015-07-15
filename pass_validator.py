#!/bin/env python
# -*- coding: utf-8 -*-
'''
Utility for mountain pass validation
Written by Andriy Danyleiko and Liudmyla Kislitsyna
Send bugs to andrii.danyleiko@gmail.com or by github https://github.com/DefteZ/westra2osm/
'''
from __future__ import unicode_literals, division, print_function
import sys, argparse, codecs
import datetime
reload(sys)
sys.setdefaultencoding('utf-8')
#another way sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

import lxml.html

import westra2osm_lib
from westra2osm_lib import *

def main():
    parser = createParser()
    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)
    cli_args = parser.parse_args()
    global debug_mode
    debug_mode = cli_args.debug
    
    if debug_mode: print('\nDEBUG: parsed arguments is:\n{0}\n'.format(cli_args))
    
    if cli_args.poly:
        poly = []
        for point in cli_args.poly.split():
            coord = point.split(',')
            assert len(coord) == 2
            coord = tuple((float(coord[0]), float(coord[1])))
            poly.append(coord)
        else:
            poly = tuple(poly)
    elif cli_args.sas_polygon:
        poly = parse_sas_polygon(cli_args.sas_polygon)
    else:
        print('ERROR: please define polygon\n')
        sys.exit(1)
    
    bbox = poly2bbox(poly)
    
    if debug_mode:
        print('\nDEBUG: Parsed polygon is\n{0}\n'.format(','.join((str(x) for x in poly))))
        print('\nDEBUG: Generated BBOX is\n{0}\n'.format(bbox))
    
    westra_kml_passes = get_pass_westra(*bbox)
    osm_passes = get_pass_from_overpass(*bbox)
    
    #parsing kml points to MountainPass objects
    westra_passes = []
    mountain_numb = 0
    for p in westra_kml_passes:
        if p.name.startswith('вер. '):
            mountain_numb += 1
            continue
        name = p.name.lstrip('пер. ')
        saddle = MountainPass(name)
        
        #check alt_names
        root = lxml.html.fromstring(p.description)
        rows = root.xpath("table")[0].findall("tr")
        alt_names_text = rows[1].getchildren()[1].text
        if alt_names_text:
            alt_names = [p.strip() for p in alt_names_text.split(',')]
            saddle.alt_names = alt_names
        westra_passes.append(saddle)
    
    #for statistics and validation
    all_westra = len(westra_passes)
    all_osm = len(osm_passes)
    osm_alone = 0
    both_base = 0
    
    #recurcive searching
    d_passes = {}
    for p in osm_passes:
        name = p['name']
        saddle = MountainPass(name)
        if p.get('alt_name'):
            alt_names = [name.strip() for name in  p['alt_name'].split(';')]
            saddle.alt_names = alt_names
        
        for s in westra_passes:
            if s.names() & saddle.names():
                d_passes[saddle.name] = s.human_names(), saddle.human_names()
                westra_passes.remove(s)
                both_base += 1
                break
        else:
            d_passes[saddle.name] = '', saddle.human_names()
            osm_alone += 1
    
    # додаєм перевали з вестри яких немає на осм.
    westra_alone = len(westra_passes)
    for s in westra_passes:
        d_passes[s.name] = s.human_names(), ''
    
    assert len(westra_kml_passes) == both_base+westra_alone+mountain_numb, 'sometching goes wrong with Westra DB: {0} != {1}+{2}+{3}'.format(len(westra_kml_passes), both_base, westra_alone, mountain_numb)  #self-check
    
    # вибираєм куда писать
    if cli_args.file:
        f = codecs.open(cli_args.file, "w", encoding="utf-8")
    else:
        f = sys.stdout
    
    #write header
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M EET")
    f.write ('''<!DOCTYPE HTML>
<html>
<title>OSM валідатор перевалів</title>
<meta charset="utf-8">
<meta name="keywords" content="Вестра, OSM, Openstreetmap, westra, kml"> 
<body>
<b>Останній раз оновлено:</b> {0}<br>
Вього перевалів в таблиці: {all_pass}<br>
\tіз них є тільки в Вестрі: {only_westra}<br>
\tіз них є тільки в OSM: {only_osm}<br>
\tє в обох базах: {both}<br>
<a href='https://github.com/DefteZ/westra2osm/'>Дізнаться більше про проект</a><br>
<br>
<table border>
<tr><th>Перевал в каталогі "Вестри"</th><th>Перевал в ОСМ</th></tr>'''.format(date_str, all_pass=westra_alone+osm_alone+both_base, only_westra=westra_alone, only_osm=osm_alone, both=both_base))
    
    dkeys = d_passes.keys()
    dkeys.sort()
    
    for k in dkeys:
        f.write('''        <tr><td>{0!s}</td><td>{1!s}</td></tr>\n'''.format(*d_passes[k]))
    
    #write footer
    f.write('    </table>\n    </body>\n    </html>\n')


def createParser():
    '''create cli options'''
    myFormater = lambda prog: argparse.RawDescriptionHelpFormatter(prog,max_help_position=25,width=190)
    parser = argparse.ArgumentParser(formatter_class=myFormater)
    parser.add_argument('--debug', help='Turn on debug mode', action='store_true')
    polygon_group = parser.add_mutually_exclusive_group()
    polygon_group.add_argument('-p', '--poly', help='Polygon of area that will be used for validation. Point should be splited by spaces. Format "lat1,lon1 lat2,lon2 ...".  Example "14.01,10.1 15,10.5 14.5,12.7"')
    polygon_group.add_argument('-s', '--sas-polygon', help='File with polygon in SASplanet format', type=file)
    
    #TODO
    parser.add_argument('-f', '--file', help='File what html will be saved. If omitted, will be print html to stdout.')
    #output file format
    return parser


def parse_sas_polygon(hlg_file):
    '''Convert SASplanet .hlg files to polygon tuple
    see http://www.sasgis.org/wikisasiya/ for details
    hlg_file should be open file'''
    polygon = []
    coordinate = [None, None]
    counter = 0
    for line in hlg_file:
        if line.startswith('PointL'):
            if 'PointLat_' in line:
                coordinate[0] = float(line.split('=')[1])
                counter += 1
            elif 'PointLon_' in line:
                coordinate[1] = float(line.split('=')[1])
                counter += 1
            else:
                raise AssertionError('Unknown syntax of hlg file')
            
            if counter == 2:
                polygon.append(tuple(coordinate))
                counter = 0
    polygon.pop() # remove last point, that always duplicate first
    return tuple(polygon)

if __name__ == "__main__":
    main()
