#!/usr/bin/env python

import csv
import pickle

# this python script prepares a csv of cassette tapes from the barton collection for import into ASpace

############################################################

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)
        
# load csv data, go through each row,
# convert to python dict structure
def load_csv(filename):
    # open the metadata spreadsheet
    with open(filename, 'r', encoding='utf-8-sig') as file:
        # create a csv-reader object
        reader = csv.DictReader(file)
        csv_data = []
        for row in reader:
            row.pop('\n')
            row['Relation'] = row.pop('\nRelation (e.g., 1 of 10)')
            if '?' in row['Relation']:
                row['Relation'] = ''
            if row['Side A - Title'] == '(No information available)':
                row['Side A - Title'] = ''
            else:
                row['Side A - Title'] = row['Side A - Title'].replace('(?)','').replace('?','').strip()
            row['Side B - Title'] = row['Side B - Title'].replace('(?)','').replace('?','').strip()
            row['ID #'] = row['ID #'].lower().strip()
            csv_data.append(row)
    return csv_data

def create_title(c):
    if c['Side B - Title'] == '' and c['Side A - Title'] != '':
        title = c['ID #']+': '+c['Side A - Title']
    elif c['Side A - Title'] == '':
        title = c['ID #']+': Unidentified'
    elif ',' in c['Side A - Title']:
        title_list = c['Side A - Title'].split(',')
        if '1)' in title_list[0]:
            A_title = title_list[0].split('1)')[0].strip().strip(':')
            title = c['ID #']+': '+A_title
        else:
            title = c['ID #']+': '+title_list[0]
    elif 'side a' in c['Side A - Title'].lower():
        A_title = c['Side A - Title'].replace('Side A','').strip()
        title = c['ID #']+': '+A_title
    elif c['Side A - Title'].endswith('-A'):
        A_title = c['Side A - Title'].replace('1-A','').replace('2-A','').strip()
        title = c['ID #']+': '+A_title
    elif len(c['Side A - Title']) > 2 and c['Side A - Title'].endswith('A'):
        A_title = c['Side A - Title'].replace('1A','').replace(' A','').replace('2A','').strip()
        title = c['ID #']+': '+A_title
    else:
        title = c['ID #']+': '+c['Side A - Title']
    return title

def create_notes(c):
    sideA,sideB,rel,info = None,None,None,None
    if c['Side B - Title'] != '' and c['Side A - Title'] != '':
        sideA = '<p>Side A: '+c['Side A - Title']+'</p>'
    
    if c['Side B - Title'] != '':
        sideB = '<p>Side B: '+c['Side B - Title']+'</p>'
    
    if c['Relation'] != '':
        rel = '<p>Relation: '+c['Relation']+'</p>'
        
    if c['Additional Information'] != '':
        info = '<p>'+c['Additional Information']+'</p>'
        
    content_list = [sideA,sideB,rel,info]
    content = ''.join(filter(None, content_list))
    
    note_list = []
    if content != None:
        note_list = [{'jsonmodel_type': 'note_multipart',
                          'publish': False,
                          'subnotes': [{'content': content,
                                        'jsonmodel_type': 'note_text',
                                        'publish': False}],
                          'type': 'scopecontent'}]
    return note_list

############################################################

cassettes = load_csv('./data/barton_cassettes.csv')
print('loaded '+str(len(cassettes))+' cassettes')
series_uri = '/repositories/2/archival_objects/4285'
ao_list = []
for c in cassettes:
    kb_ao = {}
    kb_ao['ancestors'] = [{'level': 'series', 'ref': series_uri},
                          {'level': 'collection', 'ref': '/repositories/2/resources/4'}]
    kb_ao['jsonmodel_type'] = 'archival_object'
    kb_ao['level'] = 'item'
    kb_ao['notes'] = create_notes(c)
    kb_ao['publish'] = False
    kb_ao['repository'] = {'ref': '/repositories/2'}
    kb_ao['resource'] = {'ref': '/repositories/2/resources/4'}
    kb_ao['title'] = create_title(c)
    kb_ao['parent'] = {'ref': series_uri}
    ao_list.append(kb_ao)

print('created '+str(len(ao_list))+' archival objects')

write_pickle(ao_list, './data/cassettes.txt')

print('data ready for import!')

