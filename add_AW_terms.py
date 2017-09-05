#!/usr/bin/env python

import pickle
import csv 

# this python script takes in a list of resources with subject tags (from HRAF & LCSH) and uses those subjects to add AW browsing terms by subject ID on ASpace

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)

############################################################

# load resources
filename = input("Enter the path to the data file containing the downloaded resource records (e.g. ./data/ethno.txt): ")

resources = load_pickled(filename)

print('will add AW browsing terms to '+str(len(resources))+' resource records')

# add performing arts to resources with "performance" in the title or notes
# add native american to resources with similar subjects
# add washington state to resources with geographically relevant subject terms
# add music, anthropology, and sound recordings to ethnomusicology collections
for i in resources:
    # performing arts = 530 (aw)
    if 'performance' in i['title'].lower() or any('performance' in d['subnotes'][0]['content'].lower() for d in i['notes'] if 'subnotes' in d) or any('performance' in d['content'][0].lower() for d in i['notes'] if 'content' in d):
        i['subjects'].append({'ref': '/subjects/530'})
    # american indian = 10, Native American Music = 318
    # 526 = native am (aw)
    am_ind_subs = ['/subjects/10', '/subjects/318']
    if any(d['ref'] in am_ind_subs for d in i['subjects']):
        i['subjects'].append({'ref': '/subjects/526'})
    # lushootseed = 123, coast salish = 379, NW Coast Indians = 147
    # washington state = 563 (aw)
    nw_ind = ['/subjects/123', '/subjects/379', '/subjects/147']
    if any(d['ref'] in nw_ind for d in i['subjects']):
        i['subjects'].append({'ref': '/subjects/526'})
        i['subjects'].append({'ref': '/subjects/563'})
    # 524 = Music (aw), 471 = Anthro (aw), sound rec = 1852 (aw)
    i['subjects'].append({'ref': '/subjects/524'})
    i['subjects'].append({'ref': '/subjects/471'})
    i['subjects'].append({'ref': '/subjects/1852'})

print('successfully matched '+str(len(resources))+' agent names to lcnaf names')

output = input("enter the path and name of the data file to store your list of resources in (e.g. ./data/updates.txt): ")
write_pickle(resources, output)
print('data saved!')

