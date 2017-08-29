#!/usr/bin/env python

import pickle
import re

# this python script takes in all agent-people from ASpace and cleans up those imported using the lcnaf plugin 
# outputs a list of corrected agent records to update

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)

############################################################

filename = input("Enter the path to the data file containing the downloaded agent records (e.g. ./data/people.txt or ./data/corp.txt): ")

agents = load_pickled(filename)

# limit to recently imported items from the lcnaf plugin (based on source)
naf = [i for i in agents if any(n['source'] == 'naf' for n in i['names']) or any(n['source'] == 'ingest' for n in i['names'])]

if 'people' in filename:
	updates =[]
	# remove extra () and , and whitespace from fuller name and rest of name
	# make sure source is lcnaf 
	for agent in naf:
		for name in agent['names']:
			if name['source'] != 'lcnaf':
				name['source'] = 'lcnaf'
				if 'fuller_form' in name and not re.match(r'^\w+$', name['fuller_form']):
					name['fuller_form'] = re.sub('[,\(\)]', '', name['fuller_form']).strip()
				if 'rest_of_name' in name and not re.match(r'^\w+$', name['rest_of_name']):
					name['rest_of_name'] = re.sub('[,\(\)]', '', name['rest_of_name']).strip()
		# make sure display name matches 1st name
		agent['display_name']['source'] = agent['names'][0]['source']
		if 'rest_of_name' in agent['display_name']:
			agent['display_name']['rest_of_name'] = agent['names'][0]['rest_of_name']
		if 'fuller_form' in agent['display_name']:
			agent['display_name']['fuller_form'] = agent['names'][0]['fuller_form']
		updates.append(agent)

elif 'corp' in filename:
	updates =[]
	# remove extra () and , and whitespace from subordinate_name_1, remove primary name ending '.' (ASpace adds one in to display name)
	# make sure source is lcnaf 
	for agent in naf:
		for name in agent['names']:
			if name['source'] != 'lcnaf':
				name['source'] = 'lcnaf'
				if name['primary_name'].endswith('.'):
					name['primary_name'] = name['primary_name'][:-1].strip()
				if 'subordinate_name_1' in name and not re.match(r'^\w+$', name['subordinate_name_1']):
					name['subordinate_name_1'] = re.sub('[\.,\(\)]', '', name['subordinate_name_1']).strip()
		# make sure display name matches 1st name
		agent['display_name']['source'] = agent['names'][0]['source']
		agent['display_name']['primary_name'] = agent['names'][0]['primary_name']
		if 'subordinate_name_1' in agent['display_name']:
			agent['display_name']['subordinate_name_1'] = agent['names'][0]['subordinate_name_1']
		updates.append(agent)

print('successfully cleaned up '+str(len(updates))+' agent names')

output = input("enter the path and name of the data file to store your saved agents in (e.g. ./data/updates.txt): ")
write_pickle(updates, output)
print('data saved!')
