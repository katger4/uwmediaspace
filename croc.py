#!/usr/bin/env python

import json
from collections import OrderedDict
import xmltodict
from itertools import groupby

# this python script prepares an Archives West converted xml document for EAD validation

############################################################

def dict2xmlstr(mergeddata,pretty=False):
    fulltext = json.dumps(mergeddata)
    jsonObj = json.JSONDecoder(object_pairs_hook=OrderedDict).decode(fulltext)
    xmlStr = xmltodict.unparse(jsonObj,pretty=pretty)
    return xmlStr

def write_EAD_xml(xmlstr, outfilename):
    with open(outfilename, 'w') as outfile:
        outfile.write(xmlstr[0:39])
        outfile.write('<!DOCTYPE ead PUBLIC "+//ISBN 1-931666-00-8//DTD ead.dtd (Encoded Archival Description (EAD) Version 2002)//EN" "ead.dtd">')
        outfile.write('\n')
        outfile.write(xmlstr[39:])

def parse_series(seriesidx):
    # suppress subseries items
    # add genre to general note for visibility
    for d in series[seriesidx]['c02']:
        if d['@level'] == 'subseries' and 'c03' in d:
            d.pop('c03')

        genres = []
        if 'controlaccess' in d:
            if type(d['controlaccess']['genreform']) is list:
                for g in d['controlaccess']['genreform']:
                    genre = g['#text']
                    genres.append(genre)
            else:
                genre = d['controlaccess']['genreform']['#text']
                genres.append(genre)

        if 'odd' in d and genres != []:
            d['odd']['p'] = 'Genres: '+'; '.join(genres)
        elif 'odd' not in d and genres != []:
            d['odd'] = {'@encodinganalog':'500',
                        'p': 'Genres: '+'; '.join(genres)}
        elif 'odd' in d and genres == []:
            d.pop('odd')

    list_of_items = series[seriesidx]['c02']

    titles = set([d['did']['unittitle']['#text'] for d in list_of_items])
    print(len(titles))

    new_items = []

    for k,v in groupby(list_of_items, key=lambda d:d['did']['unittitle']['#text']):
        items = list(v)
        if len(items) == 1:
            if items[0]['@level'] == 'item':
                items[0]['did']['physdesc'] = {'extent': {'@encodinganalog': '300$a'}}
                if 'Audio' in series[seriesidx]['did']['unittitle']['#text']:
                    items[0]['did']['physdesc']['extent']['#text'] = '1 audio file'
                elif 'Video' in series[seriesidx]['did']['unittitle']['#text']:
                    items[0]['did']['physdesc']['extent']['#text'] = '1 video file'
                new_items.append(items[0])
            else:
                items[0]['@level'] = 'item'
                new_items.append(items[0])
        else:
            first = items[0]
            
            dates = [d['did']['unitdate'] for d in items if 'unitdate' in d['did']]
            first['did']['unitdate'] = dates

            if any(d['@level'] == 'subseries' for d in items):
                extent_num = 0
                for d in items:
                    if d['@level'] == 'subseries':
                        extent_list = d['did']['physdesc']['extent']['#text'].split(' ')
                        series_extent = int(extent_list[0])
                        extent_num += series_extent
                    else:
                        extent_num += 1
                extent_num = str(extent_num)
            else:
                extent_num = str(len(items))

            first['did']['physdesc'] = {'extent': {'@encodinganalog': '300$a'}}

            if 'Audio' in series[seriesidx]['did']['unittitle']['#text']:
                first['did']['physdesc']['extent']['#text'] = extent_num+' audio files'
            elif 'Video' in series[seriesidx]['did']['unittitle']['#text']:
                first['did']['physdesc']['extent']['#text'] = extent_num+' video files'

            first['@level'] = 'item'
            new_items.append(first)

    print(len(new_items))

    series[seriesidx]['c02'] = new_items

############################################################

# load converted EAD
# path = input("enter the path and name of the xml file converted using the archives west utility (e.g. ./data/converted_ead.xml): ")
path = './data/wau_uwea_2008012-temp.xml'
with open(path) as fd:
    doc = xmltodict.parse(fd.read())

# locate the series containing archival objects
series = doc['ead']['archdesc']['dsc']['c01']

# # indicate how many series of archival objects to parse
# num_series = int(input("enter the number of series containing archival objects to reformat: "))
num_series = 2

while num_series > 0:
    title = input("enter the title of a series containing archival objects (e.g. Sound Recordings): ")

    for idx,i in enumerate(series):
        if title in i['did']['unittitle']['#text']:
            seriesidx = idx

    parse_series(seriesidx)
    num_series -= 1

# convert dict to json to xmlstring
xmlstr = dict2xmlstr(doc, pretty = True)

output = input("enter the path and name of the data file to store your prepped EAD in (e.g. ./data/wau_eadname.xml): ")
write_EAD_xml(xmlstr, output)
print('EAD saved!')
