#!/usr/bin/env python

import pickle

# this python script takes in Aspace subjects and spits out the names of subjects duplicated by the LCNAF plugin import process

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

############################################################

subs = load_pickled('./data/subjects.txt')

loc = [i for i in subs if i['source'] == 'Library of Congress Subject Headings' or i['source'] == 'lcsh']

print('there are '+str(len(loc))+' subjects to check for duplicates')

seen = []

for i in loc:
    if i['title'] not in seen:
        seen.append(i['title'])
    else:
        print(i['title'])