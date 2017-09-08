#!/usr/bin/env python

import json
from collections import OrderedDict
import xmltodict

# this python script prepares the Barton collection for import to AW

############################################################

def is_digi(year):
    if year.isdigit() and year > '2008':
        return True
    else:
        return False

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
    for d in series[seriesidx]['c02'][:5]:
        if 'dao' in d['did']:
            d['did']['dao'].pop('@actuate')
            d['did']['dao'].pop('@type')
            d['did']['dao'].pop('daodesc')

        if 'scopecontent' in d: 
            if 'p' not in d['scopecontent'] and 'list' not in d['scopecontent']:
                d['scopecontent']['p'] = {'p': d['scopecontent']['#text']}
                d['scopecontent'].pop('#text')
            # turn multi-p scope notes into scope list for display (no newline between notes otherwise)
            elif 'p' in d['scopecontent'] and type(d['scopecontent']['p']) is list:
                scope_list = [{'p':p, '@encodinganalog': '5202_'} for p in d['scopecontent']['p'] if not p.startswith('Information Source:')]
                d['scopecontent'] = scope_list

        # move physdesc text to gen notes so it displays
        if 'physdesc' in d['did']:
                physdesc = d['did']['physdesc']
                d['odd'] = {'@encodinganalog': '500',
                            'p': physdesc}

        # remove digitization dates for display purposes
        if 'unitdate' in d['did']:
            if type(d['did']['unitdate']) != list:
                try:
                    year = d['did']['unitdate']['#text'][:4]
                    if is_digi(year) == True:
                        d['did'].pop('unitdate')
                except TypeError:
                    year = d['did']['unitdate'][:4]
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

        # correct name sources/rules as necessary for creators
        if 'origination' in d['did']:
            if 'persname' in d['did']['origination']:
                ppl = parse_origination(d['did']['origination'], 'persname')
            if 'corpname' in d['did']['origination']:
                cor = parse_origination(d['did']['origination'], 'corpname')

def fix_altrender(subject_type, subname):
    if type(subject_type[subname]) is not list and subject_type[subname]['@source'] == 'archiveswest':
        subject_type[subname]['@altrender'] = 'nodisplay'
        subject_type[subname]['@encodinganalog'] = '690'
    elif type(subject_type[subname]) is list:
        for c in subject_type[subname]:
            if c['@source'] == 'archiveswest':
                c['@altrender'] = 'nodisplay'
                c['@encodinganalog'] = '690'

def parse_controlaccess(subject_type):
    if 'geogname' in subject_type:
        fix_altrender(subject_type, 'geogname')
    if 'genreform' in subject_type:
        fix_altrender(subject_type, 'genreform')

def parse_origination(origination, agent_type):
    creators_list = []
    if type(origination[agent_type]) != list:
        name = origination[agent_type]
        fix_agent_source(name)
        creators_list.append(name['#text'])
    else:
        for name in origination[agent_type]:
            fix_agent_source(name)
            creators_list.append(name['#text'])
    return '; '.join(creators_list)

def combine_multiple_creators(origination):
    if 'persname' in origination:
        origination.pop('persname')
    if 'corpname' in origination:
        origination.pop('corpname')
    all_creators = '; '.join(filter(None,[people,corps]))
    creator = {}
    creator['@role'] = 'creator'
    creator['@rules'] = 'aacr2'
    creator['@encodinganalog'] = '100'
    creator['#text'] = all_creators
    return creator

############################################################

# # load converted EAD
# path = input("enter the path and name of the xml file converted using the archives west utility (e.g. ./data/converted_ead.xml): ")
path = './data/wauem_2010012-c.xml'
repo = '2'

with open(path) as fd:
    doc = xmltodict.parse(fd.read())

# fix agency codes (sometimes exported strangely)
doc['ead']['eadheader']['eadid']['@mainagencycode'] = 'wauem'
doc['ead']['archdesc']['did']['unitid']['@repositorycode'] = 'wauem'

# remove unnecessary extref tag if there
if 'extref' in doc['ead']['eadheader']['filedesc']['publicationstmt']:
    doc['ead']['eadheader']['filedesc']['publicationstmt'].pop('extref')      

# remove additional dates if exist for display
# note: all ethno resources will have the creation date as the first date
# other dates (accession/publication) will be removed
# datechar not exported from ASpace, better way to identify dates would be good
resource_date = doc['ead']['archdesc']['did']['unitdate']
if type(resource_date) is list:
    doc['ead']['archdesc']['did']['unitdate'] = resource_date[0]
    # save creation date for use in title parsing below
    date_text = resource_date[0]['#text']
else:
    date_text = resource_date['#text']

# remove the date tag from the title element (seems to be displaying improperly)
# add creation date to title text if not undated
titles = doc['ead']['eadheader']['filedesc']['titlestmt']['titleproper']
for t in titles:
    if 'date' in t:
        #t.move_to_end('date') # last=False moves to beginning)
        t.pop('date')
        if date_text != 'Undated':
            t['#text'] = t['#text']+', '+date_text

# fix origination source/rules if wrong
# remove audience="internal" so displays properly
# if multiple creators, join text as a list so display of creators isn't crammed together
origination = doc['ead']['archdesc']['did']['origination']
origination.pop('@audience')

people = ''
corps = ''
if 'persname' in origination:
    people = parse_origination(origination, 'persname')
if 'corpname' in origination:
    corps = parse_origination(origination, 'corpname')

doc['ead']['archdesc']['did']['origination']['persname'] = combine_multiple_creators(origination)

# fix display settings for aw browsing terms
controlaccess = doc['ead']['archdesc']['controlaccess']['controlaccess']
if type(controlaccess) is list:
    for subject_type in controlaccess:
        parse_controlaccess(subject_type)
else:
    parse_controlaccess(controlaccess)

# if a resource contains archival objects in a series, 
# parse the objects in that series
if 'dsc' in doc['ead']['archdesc']:

    # locate the series containing archival objects
    series = doc['ead']['archdesc']['dsc']['c01']

    # indicate how many series of archival objects to parse
    # num_series = int(input("enter the number of series containing archival objects to reformat: "))
    num_series = 1

    while num_series > 0:
        # title = input("enter the title of a series containing archival objects (e.g. Sound Recordings): ")
        title = 'Reels'

        for idx,i in enumerate(series):
            if title in i['did']['unittitle']['#text']:
                seriesidx = idx

        parse_series(seriesidx)
        num_series -= 1

# convert dict to xmlstring
xmlstr = xmltodict.unparse(doc, pretty=True)

# the converter seems to change @actuate: 'onrequest' to @actuate: ''
# need to change back to onrequest
# this applies mainly to logsheet links in note text and links to documents in descriptions
# also, converter or exporter incorrectly label some source elements as 'Library of Congress Subject Headings' when should be 'lcsh'
xmlstr = xmlstr.replace('actuate=""', 'actuate="onrequest"').replace('Library of Congress Subject Headings', 'lcsh')

output = input("enter the path and name of the data file to store your prepped EAD in (e.g. ./data/wau_eadname.xml): ")
write_EAD_xml(xmlstr, output)
print('EAD saved!')
