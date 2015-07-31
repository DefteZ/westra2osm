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

import pygpx, gpxpy.gpx

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
    
    #get passes from databases
    westra_passes = get_pass_westra(*bbox) #return MountainPass instanses
    osm_passes = get_pass_from_overpass(*bbox) #return MountainPass instanses
    
    #filter westra passes with poly
    out_of_poly = []
    for i, s in enumerate(westra_passes):
        if not point_inside_polygon(*s.coordinates, poly=poly):
            out_of_poly.append(i)
    else:
        for i in reversed(out_of_poly):
            del westra_passes[i]
    
    #filter osm passes with poly
    out_of_poly = []
    for i, s in enumerate(osm_passes):
        if not point_inside_polygon(*s.coordinates, poly=poly):
            out_of_poly.append(i)
    else:
        for i in reversed(out_of_poly):
            del osm_passes[i]
    
    # create gpx
    if cli_args.file:
        gpx_filename = cli_args.file+'.gpx'
        f = codecs.open(gpx_filename, "w", encoding="utf-8")
        
        gpx_f = gpxpy.gpx.GPX()
        for wp in osm_passes:
            descr = '{0} {1}m, {2}'.format(wp.human_names(), str(wp.elevation), wp.scale)
            point = gpxpy.gpx.GPXWaypoint(*wp.coordinates, elevation=wp.elevation, name='O_'+wp.name, description=descr)  
            gpx_f.waypoints.append(point)
        else:
            f.write(gpx_f.to_xml())
            f.close()

    
    #check duplicates
    westra_dups = find_dup_in_names(westra_passes)
    osm_dups = find_dup_in_names(osm_passes)
    
    #for statistics and validation
    all_westra = len(westra_passes) - len(westra_dups)
    osm_alone = 0
    both_base = 0
    westra_alone = 0
       
    #recurcive searching
    d_passes = {}
    for osm_pass in osm_passes:
        for westra_pass in westra_passes:
            if westra_pass.names() & osm_pass.names():
                d_passes[osm_pass.name] = westra_pass.human_names_with_url(), osm_pass.human_names_with_url()
                westra_passes.remove(westra_pass)
                both_base += 1
                break
        else:
            if osm_pass.name not in d_passes:
                d_passes[osm_pass.name] = '', osm_pass.human_names_with_url()
                osm_alone += 1
    
    # додаєм перевали з вестри яких немає на осм.
    for westra_pass in westra_passes:
        if westra_pass.name not in d_passes:
            d_passes[westra_pass.name] = westra_pass.human_names_with_url(), ''
            westra_alone += 1
    
    assert all_westra == both_base+westra_alone, 'sometching goes wrong with Westra DB: {0} != {1}+{2}'.format(all_westra, both_base, westra_alone)  #self-check
    assert len(d_passes) == westra_alone+osm_alone+both_base, 'Length of dictionary is not equivalent with sum of lengths. Some passes can be missed. {0} !+ {1}+{2}+{3}'.format(len(d_passes), westra_alone, osm_alone, both_base)
    
    
    # вибираєм куда писать
    if cli_args.file:
        f = codecs.open(cli_args.file, "w", encoding="utf-8")
    else:
        f = sys.stdout
    
    #create text for duplicates
    if osm_dups:
        osm_dup_text = 'Деякі дублікацію в OSM базі, виправте це будь-ласка:<br>\n'
        for opass in osm_dups:
            osm_dup_text += ' і '.join(p.human_names_with_url() for p in opass) + '<br>\n'
        osm_dup_text += '<br>\n'
    else:
        osm_dup_text = ''
    
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
<a href='https://github.com/DefteZ/westra2osm/'>Дізнаться більше про проект</a><br>
Вього перевалів в таблиці: {all_pass}<br>
\tіз них є тільки в Вестрі: {only_westra}<br>
\tіз них є тільки в OSM: {only_osm}<br>
\tє в обох базах: {both}<br>
<br>
{odup}
<br>
<table border>
<tr><th>Перевал в каталогі "Вестри"</th><th>Перевал в ОСМ</th></tr>'''.format(date_str, all_pass=westra_alone+osm_alone+both_base, only_westra=westra_alone, only_osm=osm_alone, both=both_base, odup=osm_dup_text))
    
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


def find_dup_in_names(passes):
    '''Find MountainPass instanses with same names'''
    lpasses = passes[:]
    dubl = []
    try:
        while True:
            c_dubl = []
            cur = lpasses.pop()
            c_names = cur.names()
            for s in lpasses:
                if s.names() & c_names:
                    c_dubl.append(s)
            else:
                if c_dubl:
                    c_dubl.append(cur)
                    dubl.append(c_dubl)
    except IndexError:
        return dubl


if __name__ == "__main__":
    main()
