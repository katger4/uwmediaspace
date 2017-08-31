#!/usr/bin/env python

import pickle

# this python script adds finding aid template data to each collection in the ethnomusicology archive

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)

############################################################

# load resources
ethno = load_pickled('./data/ethno.txt')

# add template information (or filled in where possible) 
# to each collection without finding aid details filled in
updates = []
for i in ethno:
    if i['ead_id'] == '':
        i['ead_id'] = 'wau_waseumc_'+i['id_0']+'.xml'
        i['ead_location'] = 'http://archiveswest.orbiscascade.org/findaid/ark:/80444/xv[Insert ARK ID]'
        i['finding_aid_date'] = '2017'
        i['finding_aid_description_rules'] = 'dacs'
        i['finding_aid_language'] = 'Finding aid written in English.'
        if 'collection' not in i['title'].lower():
            i['finding_aid_title'] = 'Guide to the '+i['title']+' Collection'
        else:
            i['finding_aid_title'] = 'Guide to the '+i['title']
        updates.append(i)
len(updates)

print('successfully added finding aid information to '+str(len(updates))+' collections')

output = input("enter the path and name of the data file to store your saved resources in (e.g. ./data/updates.txt): ")
write_pickle(updates, output)
print('data saved!')
