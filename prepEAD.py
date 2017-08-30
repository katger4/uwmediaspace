#!/usr/bin/env python

import json
from collections import OrderedDict
import xmltodict

# this python script prepares an Archives West converted xml document for EAD validation

############################################################

def is_digi(year):
    if year.isdigit() and year > '2008':
        return True
    else:
        return False

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

############################################################

# load converted EAD
path = input("enter the path and name of the xml file converted using the archives west utility (e.g. ./data/converted_ead.xml): ")

with open(path) as fd:
    doc = xmltodict.parse(fd.read())

# fix agency codes
doc['ead']['eadheader']['eadid']['@mainagencycode'] = 'waseumc'
doc['ead']['archdesc']['did']['unitid']['@repositorycode'] = 'waseumc'

# remove unnecessary extref tag
doc['ead']['eadheader']['filedesc']['publicationstmt'].pop('extref')

# locate the series containing archival objects
series = doc['ead']['archdesc']['dsc']['c01']

title = input("enter the title of the series containing archival objects (e.g. Sound Recordings): ")

for idx,i in enumerate(series):
    if title in i['did']['unittitle']['#text']:
        seriesidx = idx

# remove extra dao tags and make sure all scopecontent has a p tag
# remove digitization dates (dont show up in AW as different dates)
for d in series[seriesidx]['c02']:
    if 'dao' in d['did']:
        d['did']['dao'].pop('@actuate')
        d['did']['dao'].pop('@type')
        d['did']['dao'].pop('daodesc')

    if 'scopecontent' in d: 
        if 'p' not in d['scopecontent']:
            d['scopecontent']['p'] = {}
            d['scopecontent']['p'] = d['scopecontent']['#text']
            d['scopecontent'].pop('#text')

    # remove digitization dates for display purposes
    if 'unitdate' in d['did']:
        if type(d['did']['unitdate']) != list:
            year = d['did']['unitdate']['#text'][:4]
            if is_digi(year) == True:
                d['did'].pop('unitdate')
        else:
            for idx,date in enumerate(d['did']['unitdate']):
                try:
                    year = date['#text'][:4]
                    if is_digi(year) == True:
                        d['did']['unitdate'].pop(idx)
                except TypeError:
                    year = date[:4]
                    if is_digi(year) == True:
                        d['did']['unitdate'].pop(idx)

# convert dict to json to xmlstring
xmlstr = dict2xmlstr(doc, pretty = True)

output = input("enter the path and name of the data file to store your prepped EAD in (e.g. ./data/wau_eadname.xml): ")
write_EAD_xml(xmlstr, output)
print('EAD saved!')
