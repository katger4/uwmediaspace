#!/usr/bin/env python

import json
from collections import OrderedDict
import xmltodict
from iso639 import languages
import re

# this python script prepares an Archives West converted xml document for EAD validation

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

# remove plural extent from items with only 1 thing (1 audiotapes --> 1 audiotape)
def parse_extent(item):
    if item.get('did',{}).get('physdesc',{}).get('extent') != None:
        extent = item['did']['physdesc']['extent']['#text']
        extent_split = extent.split(' ')
        if extent_split[0] == '1' and extent_split[-1].endswith('s'):
            extent_split[-1] = extent_split[-1][:-1]
            new_extent = ' '.join(extent_split)
            item['did']['physdesc']['extent']['#text'] = new_extent

# turn item-level multi-p notes into list for display (no newline between notes otherwise)
def expand_note(item, note_type, encodinganalog):
    if item.get(note_type, {}).get('p') != None and type(item[note_type]['p']) is list:
        item[note_type] = [{'p':p, '@encodinganalog': encodinganalog} for p in item[note_type]['p']]

# remove item-level digitization dates for display
def remove_digi(unitdate):
    if type(unitdate) != list:
        try:
            year = unitdate['#text'][:4]
            if is_digi(year) == True:
                d['did'].pop('unitdate')
        except TypeError:
            year = unitdate[:4]
            if is_digi(year) == True:
                d['did'].pop('unitdate')
    else:
        for idx,date in enumerate(unitdate):
            try:
                year = date['#text'][:4]
                if is_digi(year) == True:
                    unitdate.pop(idx)
            except TypeError:
                year = date[:4]
                if is_digi(year) == True:
                    unitdate.pop(idx)

def parse_series(seriesidx):
    # remove extra dao tags and make sure all scopecontent has a p tag
    # remove digitization dates (dont show up in AW as different dates)
    for d in series[seriesidx]['c02']:

        if 'scopecontent' in d: 
            if 'p' not in d['scopecontent'] and 'list' not in d['scopecontent']:
                d['scopecontent']['p'] = {'p': d['scopecontent']['#text']}
                d['scopecontent'].pop('#text')
            # turn multi-p scope notes into scope list for display (no newline between notes otherwise)
            expand_note(d, 'scopecontent', '5202_')

        parse_extent(d)

        # remove item-level digitization dates for display purposes
        if 'unitdate' in d['did']:
            remove_digi(d['did']['unitdate'])

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

def sort_subjects(subject_type, subname):
    if type(subject_type[subname]) is list:
        subject_type[subname] = sorted(subject_type[subname], key=lambda k: k['#text'])

def parse_controlaccess(subject_type):
    if 'geogname' in subject_type:
        fix_altrender(subject_type, 'geogname')
        sort_subjects(subject_type, 'geogname')
    if 'genreform' in subject_type:
        fix_altrender(subject_type, 'genreform')
        sort_subjects(subject_type, 'genreform')
    if 'subject' in subject_type:
        sort_subjects(subject_type, 'subject')
    if 'persname' in subject_type:
        parse_origination(subject_type, 'persname')
    if 'corpname' in subject_type:
        parse_origination(subject_type, 'corpname')

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

def combine_multiple_creators(origination, people, corps):
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

# load converted EAD
filename = input("enter the name of the xml file converted using the archives west utility stored in the data folder (e.g. converted_ead.xml): ")

with open('./data/'+filename) as fd:
    doc = xmltodict.parse(fd.read())

# remove unnecessary extref tag in publicationstmt if there
if 'extref' in doc['ead']['eadheader']['filedesc']['publicationstmt']:
    doc['ead']['eadheader']['filedesc']['publicationstmt'].pop('extref')

# add links to bioghist
for idx,p in enumerate(doc['ead']['archdesc']['bioghist']['p']):
    if '(http' in p:
        link = re.search(r'\((.*?)\)', p).group(1)
        new_p = re.sub(r'\(.*?\)', '<extref href="'+link+'" show="new" actuate="onrequest">'+link+'</extref>', p)
        doc['ead']['archdesc']['bioghist']['p'][idx] = new_p

# add additional languages if present for display (langmaterial doesn't display)
langs = doc['ead']['archdesc']['did']['langmaterial']
if type(langs) is list:
    secondlang_text = doc['ead']['archdesc']['did']['langmaterial'][1]
    firstlang = doc['ead']['archdesc']['did']['langmaterial'][0]['language']
    try:
        standard_name = languages.get(name=secondlang_text)
        code = standard_name.part3
        secondlang = {'@langcode': 'eng', 
                        '@encodinganalog': '546', 
                        '#text': secondlang_text}
        bothlanguages = [firstlang,secondlang]
        doc['ead']['archdesc']['did']['langmaterial'] = {'language': bothlanguages}
    except KeyError:
        pass        

# remove additional dates if exist for display
# note: all ethno resources will have the creation date as the first date
# other dates (accession/publication) will be removed
# datechar not exported from ASpace, better way to identify dates would be good
resource_date = doc['ead']['archdesc']['did']['unitdate']
if type(resource_date) is list:
    doc['ead']['archdesc']['did']['unitdate'] = resource_date[0]
    # save creation date for use in title parsing below
    date_text = resource_date[0]['#text']
    norm = resource_date[0]['@normal']
else:
    date_text = resource_date['#text']
    norm = resource_date['@normal']

# remove the date tag from the title element (seems to be displaying improperly)
# add creation date to title text if not undated
titles = doc['ead']['eadheader']['filedesc']['titlestmt']['titleproper']
for t in titles:
    if 'date' in t:
        #t.move_to_end('date') # last=False moves to beginning)
        t.pop('date')
        if '/' in norm:
            begin,end = norm.split('/')
        else:
            begin,end = None,None
        if date_text != 'Undated' and begin != end:
            t['#text'] = t['#text']+', '+date_text

# fix origination source/rules if wrong
# remove audience="internal" so displays properly
# if multiple creators, join text as a list so display of creators 
# isn't crammed together (without whitespace separating individuals)
origination = doc['ead']['archdesc']['did']['origination']
origination.pop('@audience')

people = ''
corps = ''
if 'persname' in origination:
    people = parse_origination(origination, 'persname')
if 'corpname' in origination:
    corps = parse_origination(origination, 'corpname')

doc['ead']['archdesc']['did']['origination']['persname'] = combine_multiple_creators(origination, people, corps)

# fix display settings for aw browsing terms
controlaccess = doc['ead']['archdesc']['controlaccess']['controlaccess']
if type(controlaccess) is list:
    for subject_type in controlaccess:
        parse_controlaccess(subject_type)
else:
    parse_controlaccess(controlaccess)

if 'dsc' in doc['ead']['archdesc']:
    top_level = doc['ead']['archdesc']['dsc']['c01']
    if type(top_level) is list:
        # if a resource contains any archival objects in a series, 
        # parse the objects in that series
        if any(c['@level'] == 'series' for c in top_level):
            # indicate how many series of archival objects to parse
            num_series = int(input("enter the number of series containing archival objects to reformat: "))
            # num_series = 2
            while num_series > 0:
                title = input("enter the title of a series containing archival objects (e.g. Sound Recordings): ")
                for idx,i in enumerate(top_level):
                    if title in i['did']['unittitle']['#text']:
                        seriesidx = idx
                parse_series(seriesidx)
                num_series -= 1
        # otherwise, if top level archival objects are items,
        # turn multi-p general notes into list for display 
        # (no newline between notes otherwise)
        if any(c['@level'] == 'item' for c in top_level):
            for d in top_level:
                expand_note(d, 'odd', '500')
                expand_note(d, 'scopecontent', '5202_')
                parse_extent(d)
    else:
        if top_level['@level'] == 'item': 
            expand_note(top_level, 'odd', '500')
            expand_note(top_level, 'scopecontent', '5202_')
            parse_extent(top_level)

# convert dict to xmlstring
xmlstr = xmltodict.unparse(doc, pretty=True)

# the converter seems to change @actuate: 'onrequest' to @actuate: ''
# need to change back to onrequest
# this applies mainly to logsheet links in note text and links to documents in descriptions
# also, converter or exporter incorrectly label some source elements as 'Library of Congress Subject Headings' when should be 'lcsh'
xmlstr = xmlstr.replace('actuate=""', 'actuate="onrequest"').replace('Library of Congress Subject Headings', 'lcsh').replace('&gt;','>').replace('&lt;','<')

output = input("enter the name your new EAD document to be output into the data folder (e.g. wau_eadname.xml): ")
write_EAD_xml(xmlstr, './data/'+output)
print('EAD saved!')
