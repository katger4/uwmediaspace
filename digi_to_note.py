#!/usr/bin/env python

import pickle

# this python script extracts digitization information from the date field of archival objects and adds it to the notes field (digitization dates do not display properly in AW)

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)

############################################################

# load aos
aos = load_pickled('./data/aos.txt')

updates = []
for i in mr_aos:
	# extract the digitized date text
    for d in i['dates']:
        if d['label'] == 'digitized':
            if 'expression' in d:
                digidate = '<p>Digitized on '+d['expression']+'.</p>'
            else:
                digidate = '<p>Digitized on '+d['begin']+'.</p>'
        else:
            digidate = ''
    # check if a scope note does not exist --> create it if not
    if not any(n['type'] == 'scopecontent' for n in i['notes']) and digidate != '':
        i['notes'].append({'jsonmodel_type': 'note_multipart',
                           'publish': False,
                           'subnotes': [{'content': digidate,
                                         'jsonmodel_type': 'note_text',
                                         'publish': False}],
                           'type': 'scopecontent'})
        updates.append(i)
    # if a scope note does exist, add to it
    elif any(n['type'] == 'scopecontent' for n in i['notes']):
        for n in i['notes']:
            if n['type'] == 'scopecontent' and digidate != '':
                formatted = '<p>'+n['subnotes'][0]['content']+'</p>'
                n['subnotes'][0]['content'] = formatted+digidate
                updates.append(i)

print('successfully added digitization information to the notes of '+str(len(updates))+' AOs')

output = input("enter the path and name of the data file to store your saved archival objects in (e.g. ./data/updates.txt): ")
write_pickle(updates, output)
print('data saved!')
