#!/usr/bin/env python

import json
from collections import OrderedDict
import xmltodict
import re
import configparser

# this python script prepares the Barton collection for import to AW

############################################################

# turn item-level multi-p notes into list for display (no newline between notes otherwise)
def expand_note(item, note_type, encodinganalog):
    if item.get(note_type, {}).get('p') != None and type(item[note_type]['p']) is list:
        item[note_type] = [{'p':p, '@encodinganalog': encodinganalog} for p in item[note_type]['p'] if p != None and not p.startswith('Information Source:')]

############ date functions ############
# check if a second date is actually digitization date
def is_digi(year):
    if year.isdigit() and year > '2008':
        return True
    else:
        return False

# remove item-level digitization dates for display
def remove_digi(d, unitdate):
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
############ date functions ############

############ subject functions ############
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
############ subject functions ############

############ agent functions ############
def read_agent_relators(text_file):
    with open(text_file) as f:
        content = f.readlines()
        relators = {}
        for line in content:
            k,v = line.strip().split(': ')
            relators[k] = v
        return relators

def correct_relator_abbreviations(name, relators):
    if '@role' in name:
        name['@role'] = relators[name['@role']].lower()

def fix_agent_source(name):
    if '@source' in name and name['@source'] != 'lcnaf':
        if '@rules' in name and name['@rules'] == 'aacr2':
            name.pop('@source')
        else:
            name['@rules'] = 'aacr2'
            name.pop('@source')

def parse_origination(origination, agent_type):
    creators_list = []
    if type(origination[agent_type]) != list:
        name = origination[agent_type]
        fix_agent_source(name)
        correct_relator_abbreviations(name, relators)
        creators_list.append(name['#text'])
    else:
        for name in origination[agent_type]:
            fix_agent_source(name)
            correct_relator_abbreviations(name, relators)
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
############ agent functions ############

def parse_series(seriesidx):
    # remove extra dao tags and make sure all scopecontent has a p tag
    # remove digitization dates (dont show up in AW as different dates)
    for d in series[seriesidx]['c02']:

        if 'scopecontent' in d: 
            if 'p' not in d['scopecontent'] and 'list' not in d['scopecontent']:
                d['scopecontent']['p'] = {'p': d['scopecontent']['#text']}
                d['scopecontent'].pop('#text')
            if 'p' in d['scopecontent'] and type(d['scopecontent']['p']) is not list and 'Information Source: ' in d['scopecontent']['p']:
                d.pop('scopecontent')
            
            expand_note(d, 'scopecontent', '5202_')

        # add a reel's unit id to each item if it is not there, based on the item's title
        regexp = re.compile(r'Reel\s(\d{5}):\s')
        if 'unitid' not in d['did'] and regexp.search(d['did']['unittitle']['#text']):
        	reel_num = regexp.search(d['did']['unittitle']['#text']).group(1)
        	d['did']['unitid'] = 'barton_reel_'+reel_num

        # move physdesc text to gen notes so it displays
        if 'physdesc' in d['did']:
                physdesc = d['did']['physdesc']
                d['odd'] = {'@encodinganalog': '500',
                            'p': physdesc}

        # remove digitization dates for display purposes
        if 'unitdate' in d['did']:
            remove_digi(d, d['did']['unitdate'])

        # correct name sources/rules as necessary for creators
        if 'origination' in d['did']:
            if type(d['did']['origination']) is not list:
                if 'persname' in d['did']['origination']:
                    parse_origination(d['did']['origination'], 'persname')
                if 'corpname' in d['did']['origination']:
                    parse_origination(d['did']['origination'], 'corpname')
            else:
                for o in d['did']['origination']:
                    if 'persname' in o:
                        parse_origination(o, 'persname')
                    if 'corpname' in o:
                        parse_origination(o, 'corpname')
    
    # sort items in series by unit id (if unit id exists)
    series[seriesidx]['c02'] = sorted(series[seriesidx]['c02'], key=lambda k: ('unitid' not in k['did'], k['did'].get('unitid')))

def write_EAD_xml(xmlstr, outfilename):
    with open(outfilename, 'w') as outfile:
        outfile.write(xmlstr[0:39])
        outfile.write('<!DOCTYPE ead PUBLIC "+//ISBN 1-931666-00-8//DTD ead.dtd (Encoded Archival Description (EAD) Version 2002)//EN" "ead.dtd">')
        outfile.write('\n')
        outfile.write(xmlstr[39:])

############################################################

# load file origin/destingation configuration
config = configparser.ConfigParser()
config.read('./data/EAD_settings.cfg')

# load agent relators conversion
relators = read_agent_relators('./data/agent_relators.txt')

# load converted EAD
filename = input("enter the name of the xml file converted using the archives west utility stored in the Downloads folder (e.g. converted_ead.xml): ")

repo = '2'

with open(config['Paths']['origin']+filename) as fd:
    doc = xmltodict.parse(fd.read())    

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

# locate the series containing archival objects
series = doc['ead']['archdesc']['dsc']['c01']

# indicate how many series of archival objects to parse
num_series = int(input("enter the number of series containing archival objects to reformat: "))

while num_series > 0:
    
    title = input("enter the title of a series containing archival objects (e.g. Reels, Cassettes): ")

    for idx,i in enumerate(series):
        if title in i['did']['unittitle']['#text']:
            seriesidx = idx

    parse_series(seriesidx)

    num_series -= 1

# convert dict to xmlstring
xmlstr = xmltodict.unparse(doc, pretty=True)

# remove id from title for display
xmlstr = re.sub('Reel\s\d{5}:\s', '', xmlstr)

# the converter seems to change @actuate: 'onrequest' to @actuate: ''
# need to change back to onrequest
# this applies mainly to logsheet links in note text and links to documents in descriptions
# also, converter or exporter incorrectly label some source elements as 'Library of Congress Subject Headings' when should be 'lcsh'
xmlstr = xmlstr.replace('actuate=""', 'actuate="onrequest"').replace('Library of Congress Subject Headings', 'lcsh')

write_EAD_xml(xmlstr, config['Paths']['destination']+filename)
print('EAD saved!')
