#!/usr/bin/env python

import pickle
import csv
import json
import requests
from progress.spinner import Spinner

# this python script takes in a list of resources from an ASpace repo and outputs a csv containing the title, id, creator/s, and uri of all resources without an ARK ID (i.e. those that have not been added to Archives West)

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def get_item(location):
    return requests.get(backendURL + location,  headers=headers).json()

# write a list of dicts to a csv file
def write_csv(data, output, fieldnames):
    with open(output, 'w', encoding='utf-8-sig') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        dict_writer.writeheader()
        dict_writer.writerows(data)

############################################################

# load resources
filename = input('enter the path to the saved list of resources (e.g. ./data/resources.txt): ')
resources = load_pickled(filename)

# connect to the AS API
backendURL = 'http://localhost:8089'

password = input("Enter the administrative password: ")

# inital request for session
connectASpace = requests.post('http://localhost:8089/users/admin/login', data = {"password":password})

if connectASpace.status_code == 200:
    print("Successfully connected to the ASpace backend!")
    sessionID = connectASpace.json()["session"]
    headers = {'X-ArchivesSpace-Session': sessionID}
else:
    print(connectASpace.status_code)

spinner = Spinner('preparing resource information for csv output...')
state = 'loading'

not_in_AW = []
while state != 'FINISHED':
	for i in resources:
		# resources on AW will have an ARK ID
		if '[Insert ARK ID]' in i['ead_location']:
			# make a list of creators, extract the display name for each, merge into a single string for csv output
			creators = [get_item(agent['ref']) for agent in i['linked_agents'] if agent['role'] == 'creator']
			creator_names = [n['display_name']['sort_name'] for n in creators]
			creator_str = '; '.join(sorted(creator_names))

			# create a dict from each resource not in AW
			not_in_AW.append({
				'title': i['title'],
				'id': i['id_0'],
				'creators': creator_str,
				'uri': i['uri']
				})

			spinner.next()

		else:
			spinner.next()
	state = 'FINISHED'

if not_in_AW != []:
	print(str(len(not_in_AW))+' resources are not yet on Archives West')

	# sort list of dicts by key
	sorted_not_in_AW = sorted(not_in_AW, key=lambda k: k['id']) 
	# create list of fieldnames in order for csv creation
	fieldnames = ['title', 'id', 'creators', 'uri']

	output = input("enter the path and name of the data file to store your csv file in (e.g. ./data/not_in_AW.csv): ")
	write_csv(sorted_not_in_AW, output, fieldnames)

	print('data saved!')
