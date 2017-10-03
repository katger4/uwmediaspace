#!/usr/bin/env python

import json
import requests
import pickle

# this python3 script converts a newline-delimited text file containing subject terms to a list of ASpace formatted dicts (json-style)

def load_txt_file(filename):
    with open(filename) as f:
        content = f.readlines() 
        return [x.strip() for x in content]

# take in a list of terms, convert to a list of structured subjects
def structure_subjects(term_list, source, term_type):
	# structure each subject as a json
	sub_list = []
	for term in term_list:
	    subject = {'jsonmodel_type': 'subject',
	               'publish': False,
	               'source': source,
	               'terms': [{'jsonmodel_type': 'term',
	                          'term': term,
	                          'vocabulary': '/vocabularies/1',
	                          'term_type': term_type}],
	               'title': term,
	              'vocabulary': '/vocabularies/1'}
	    sub_list.append(subject)
	return sub_list

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)

filename = input("Enter the path to the text file containing subject terms (e.g. ./data/nwda_material_types.txt): ")
print("loading the text file...")
term_list = load_txt_file(filename)
source = input("Enter the source of these terms (e.g. nwda, lcsh, or ehraf): ")
term_type = input("Enter the type of these terms (options are: cultural_context, function, genre_form, geographic, occupation, style_period, technique, temporal, topical, and uniform_title): ")
print("resrtucturing the subjects for import into ASpace...")
subject_list = structure_subjects(term_list, source, term_type)
output = input("Enter the path and name of the data file to store your saved subjects in (e.g. ./data/subjects.txt): ")
write_pickle(subject_list, output)


# topics = load_txt_file('./data/nwda_topics.txt')
# places = load_txt_file('./data/nwda_places.txt')
# materials = load_txt_file('./data/nwda_material_types.txt')
