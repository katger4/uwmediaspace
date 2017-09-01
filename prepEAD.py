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

def fix_lcsh(subject_type, subname):
    if type(subject_type[subname]) is not list and subject_type[subname]['@source'] == 'Library of Congress Subject Headings':
        subject_type[subname]['@source'] = 'lcsh'
    elif type(subject_type[subname]) is list:
        for c in subject_type[subname]:
            if c['@source'] == 'Library of Congress Subject Headings':
                c['@source'] = 'lcsh'

def fix_altrender(subject_type, subname):
    if type(subject_type[subname]) is not list and subject_type[subname]['@source'] == 'archiveswest':
        subject_type[subname]['@altrender'] = 'nodisplay'
    elif type(subject_type[subname]) is list:
        for c in subject_type[subname]:
            if c['@source'] == 'archiveswest':
                c['@altrender'] = 'nodisplay'

def parse_controlaccess(subject_type):
    # if 'corpname' in subject_type:
    #     fix_lcsh(subject_type, 'corpname')
    if 'geogname' in subject_type:
        fix_altrender(subject_type, 'geogname')
    # if 'subject' in subject_type:
    #     fix_lcsh(subject_type, 'subject')
    if 'genreform' in subject_type:
        fix_altrender(subject_type, 'genreform')

############################################################

# load converted EAD
path = input("enter the path and name of the xml file converted using the archives west utility (e.g. ./data/converted_ead.xml): ")
# path = './data/wau_uwea_2008012-c.xml'

with open(path) as fd:
    doc = xmltodict.parse(fd.read())

# fix agency codes
# if repo == 'media':
doc['ead']['eadheader']['eadid']['@mainagencycode'] = 'waseumc'
doc['ead']['archdesc']['did']['unitid']['@repositorycode'] = 'waseumc'

# remove unnecessary extref tag if there
if 'extref' in doc['ead']['eadheader']['filedesc']['publicationstmt']:
    doc['ead']['eadheader']['filedesc']['publicationstmt'].pop('extref')

# fix origination source/rules if wrong
# remove audience="internal" so displays properly
origination = doc['ead']['archdesc']['did']['origination']
if type(origination) != list:
    origination.pop('@audience')
    name = origination['persname']
    fix_agent_source(name)
else:
    for p in origination:
        p.pop('@audience')
        name = p['persname']
        fix_agent_source(name)

# fix incorrect lcsh subject source (occasionally exported as 'Library of Congress Subject Headings' rather that 'lcsh') and display settings for aw browsing terms
controlaccess = doc['ead']['archdesc']['controlaccess']['controlaccess']
if type(controlaccess) is list:
    for subject_type in controlaccess:
        parse_controlaccess(subject_type)
else:
    parse_controlaccess(controlaccess)


# locate the series containing archival objects
series = doc['ead']['archdesc']['dsc']['c01']

# # indicate how many series of archival objects to parse
num_series = int(input("enter the number of series containing archival objects to reformat: "))
# num_series = 2

while num_series > 0:
    title = input("enter the title of a series containing archival objects (e.g. Sound Recordings): ")

    for idx,i in enumerate(series):
        if title in i['did']['unittitle']['#text']:
            seriesidx = idx

    parse_series(seriesidx)
    num_series -= 1

# convert dict to json to xmlstring
xmlstr = dict2xmlstr(doc, pretty = True)
# the converter seems to change @actuate: 'onrequest' to @actuate: ''
# need to change back to onrequest
# this applies mainly to logsheet links in note text and links to documents in descriptions
# also, converter or exporter incorrectly label some source elements as 'Library of Congress Subject Headings' when should be 'lcsh'
xmlstr = xmlstr.replace('actuate=""', 'actuate="onrequest"').replace('Library of Congress Subject Headings', 'lcsh')

output = input("enter the path and name of the data file to store your prepped EAD in (e.g. ./data/wau_eadname.xml): ")
write_EAD_xml(xmlstr, output)
print('EAD saved!')
