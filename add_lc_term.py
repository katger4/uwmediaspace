#!/usr/bin/env python

import pickle
import csv 

# this python script takes in a QC'd tsv of geographic or topical names, as well as the list of subject records on aspace, then corrects subject records with lc terms

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def load_csv(filename):
	with open(filename, 'r', encoding='utf-8-sig') as file:
		# create a csv-reader object
		reader = csv.reader(file, delimiter='\t')
		# loop through each row in the csv-reader object
		# create a dict of name:lcnaf
		data = {row[0]: row[1] for row in reader}
	return data

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)

############################################################

# load subjects
filename = input("Enter the path to the data file containing the downloaded records (e.g. ./data/subjects.txt): ")
# filename = './data/people.txt'

subjects = load_pickled(filename)

source_limit = input('enter the exact name of the subject-source to focus on (e.g. local): ')
subjects = [i for i in subjects if i.get('source') == source_limit]

lcnaf_filename = input("Enter the path to the data file containing the lcnaf records (e.g. ./data/likely.tsv): ")

lcnaf = load_csv(lcnaf_filename)

print('will match '+str(len(lcnaf))+' lcnaf names to subject records')

sub_type = input('Enter the type of terms (geographic or topical): ')

updates = []

for sub in subjects:

	lookup_name = sub['title']
	
	if lookup_name in lcnaf:

		lcnaf_name = lcnaf[lookup_name]
		sub['source'] = 'lcsh'
		sub['title'] = lcnaf_name
		sub['terms'][0]['term'] = lcnaf_name

		if sub_type == 'geographic':
			sub['terms'][0]['term_type'] = 'geographic'
		else:
			sub['terms'][0]['term_type'] = 'topical'

		updates.append(sub)

print('successfully matched '+str(len(updates))+' subject names to LoC terms')

if updates != []:
	output = input("enter the path and name of the data file to store your saved subjects in (e.g. ./data/updates.txt): ")
	write_pickle(updates, output)
	print('data saved!')

