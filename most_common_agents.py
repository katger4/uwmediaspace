#!/usr/bin/env python

import pickle
import requests
from collections import Counter

# this python script takes in a list of archival objects (with agent links) for a certain resource and prints out a list of the top linked agent names

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def get_item(location):
    return requests.get(backendURL + location,  headers=headers).json()

def get_names(top_list, source=False):
	lc = []
	for ref,cnt in top_list:
		agent = get_item(ref)
		if source == True:
			if agent.get('display_name', {}).get('source') == 'lcnaf':
				lc.append(agent)
		else:
			lc.append(agent)
	return lc

############################################################

# load agents
filename = input("Enter the path to the data file containing the downloaded archival object records (e.g. ./data/aos.txt): ")

aos = load_pickled(filename)

# connect to the AS API
backendURL = 'http://localhost:8089'

password = input("Enter the administrative password: ")

#inital request for session
connectASpace = requests.post('http://localhost:8089/users/admin/login', data = {"password":password})

if connectASpace.status_code == 200:
    print("Successfully connected to the ASpace backend!")
    sessionID = connectASpace.json()["session"]
    headers = {'X-ArchivesSpace-Session': sessionID}
else:
    print(connectASpace.status_code)

people_links = []
corporate_links = []
for i in aos:
    if i['linked_agents'] != []:
        agents = [i['ref'] for i in i['linked_agents']]
        for a in agents:
        	if 'people' in a:
        		people_links.append(a)
        	else:
        		corporate_links.append(a)
print('found '+str(len(people_links))+' agent-person records')
print('and '+str(len(corporate_links))+' agent-corporate records')

c_people = Counter(people_links)
c_corp = Counter(corporate_links)

top_people = c_people.most_common()[:100]
top_corporate = c_corp.most_common()[:100]

limit = input('limit to agent records verified in LoC records? (y/n): ')

print('loading agents records...')

if limit == 'y':
	output_people = get_names(top_people, source=True)
	output_corporate = get_names(top_corporate, source=True)
elif limit == 'n':
	output_people = get_names(top_people)
	output_corporate = get_names(top_corporate)
else:
	print('invalid response, please try again.')

number = int(input('enter the max number of names to output: '))

for name in output_people[:number]:
	print(name['display_name']['sort_name'])

print('\n')

for name in output_corporate[:number]:
	print(name['display_name']['sort_name'])


