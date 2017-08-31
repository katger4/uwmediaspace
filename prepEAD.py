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

def fix_agent_source(name):
    if '@source' in name and name['@source'] != 'lcnaf':
        if '@rules' in name and name['@rules'] == 'aacr2':
            name.pop('@source')
        else:
            name['@rules'] = 'aacr2'
            name.pop('@source')

def parse_series(seriesidx):
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
        if 'origination' in d['did']:
            if 'persname' in d['did']['origination']:
                fix_agent_source(d['did']['origination']['persname'])
            else:
                fix_agent_source(d['did']['origination']['corpname'])
############################################################

# load converted EAD
# path = input("enter the path and name of the xml file converted using the archives west utility (e.g. ./data/converted_ead.xml): ")
# repo = input("enter the repository (media or ethno): ")
# path = './data/wau_uwea_2008012-c.xml'
path = './data/wau_croctest.xml'
repo = 'ethno'
with open(path) as fd:
    doc = xmltodict.parse(fd.read())

# fix agency codes
if repo == 'media':
    doc['ead']['eadheader']['eadid']['@mainagencycode'] = 'waseumc'
    doc['ead']['archdesc']['did']['unitid']['@repositorycode'] = 'waseumc'

# remove unnecessary extref tag if there
if 'extref' in doc['ead']['eadheader']['filedesc']['publicationstmt']:
    doc['ead']['eadheader']['filedesc']['publicationstmt'].pop('extref')

# fix origination if wrong
if type(doc['ead']['archdesc']['did']['origination']) != list:
    name = doc['ead']['archdesc']['did']['origination']['persname']
    fix_agent_source(name)
else:
    for p in doc['ead']['archdesc']['did']['origination']:
        name = p['persname']
        fix_agent_source(name)

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
