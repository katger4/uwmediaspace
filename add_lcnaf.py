#!/usr/bin/env python

import pickle
import csv 

# this python script takes in a QC'd csv of agent names & lcnaf names, as well as the list of agent records on aspace, then corrects agent records with lcnaf names

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

def correct_rules(names):
	for name in names:
		if name['source'] != 'lcnaf':
			name.pop('source')
			name['rules'] = 'aacr2'
			name['is_display_name'] = False
			name['authorized'] = False
	return names

def create_person(lcnaf_name, lcnaf_name_primary, lcnaf_name_rest, dates=None, number=None):

	agent['display_name']['source'] = 'lcnaf'
	agent['display_name'].pop('rules')
	agent['display_name']['primary_name'] = lcnaf_name_primary
	agent['display_name']['rest_of_name'] = lcnaf_name_rest

	agent['names'] = correct_rules(agent['names'])

	json_name = {'jsonmodel_type': 'name_person',
			'is_display_name': True,
			'authorized': True,
			'name_order': 'inverted',
			'primary_name': lcnaf_name_primary,
			'rest_of_name': lcnaf_name_rest,
			'sort_name': lcnaf_name,
			'source': 'lcnaf'}

	if number != None:
		json_name['number'] = number
	if dates != None:
		json_name['dates'] = dates

	agent['names'].insert(0, json_name)

############################################################

# load agents
filename = input("Enter the path to the data file containing the downloaded agent records (e.g. ./data/people.txt or ./data/corp.txt): ")
# filename = './data/people.txt'

agents = load_pickled(filename)

source_limit = input('enter the exact name of the name-source to focus on (e.g. local): ')
agents = [i for i in agents if i['display_name'].get('source') == source_limit]

lcnaf_filename = input("Enter the path to the data file containing the lcnaf records (e.g. ./data/lcnaf_fuzz.tsv): ")
# lcnaf_filename = './data/lcnaf_ppl.tsv'
lcnaf = load_csv(lcnaf_filename)

print('will match '+str(len(lcnaf))+' lcnaf names to agent records')

updates = []
if 'corp' in filename:
	for agent in agents:

		lookup_name = agent['display_name']['sort_name']
		
		if lookup_name in lcnaf:

			lcnaf_name = lcnaf[lookup_name]
			agent['display_name']['source'] = 'lcnaf'
			agent['display_name'].pop('rules')
			agent['display_name']['primary_name'] = lcnaf_name

			agent['names'] = correct_rules(agent['names'])

			json_name = {'jsonmodel_type': 'name_corporate_entity',
						'is_display_name': True,
						'authorized': True,
						'primary_name': lcnaf_name,
						'sort_name': lcnaf_name,
						'source': 'lcnaf'}

			agent['names'].insert(0, json_name)

			updates.append(agent)

elif 'people' in filename:
	for agent in agents:

		lookup_name = agent['display_name']['sort_name']
		
		if lookup_name in lcnaf:

			lcnaf_name = lcnaf[lookup_name]
			lcnaf_name_list = lcnaf_name.split(', ')

			if len(lcnaf_name_list) == 1:
				lcnaf_name_primary = lcnaf_name_list[0]
				lcnaf_name_rest = ''

			else:
				lcnaf_name_primary = lcnaf_name_list[0]
				lcnaf_name_rest = lcnaf_name_list[1]

			if len(lcnaf_name_list) in [1,2]:
				create_person(lcnaf_name, lcnaf_name_primary, lcnaf_name_rest)
				updates.append(agent)
			else:
				for n in lcnaf_name_list:
					if n in ['II','III','IV']:
						number = n
					else:
						number = None
					if any(c.isdigit() for c in n):
						dates = n
					else:
						dates = None
				create_person(lcnaf_name, lcnaf_name_primary, lcnaf_name_rest, dates, number)
				updates.append(agent)	

print('successfully matched '+str(len(updates))+' agent names to lcnaf names')

if updates != []:
	output = input("enter the path and name of the data file to store your saved agents in (e.g. ./data/updates.txt): ")
	write_pickle(updates, output)
	print('data saved!')

