#!/usr/bin/env python

import json
import requests
from progress.spinner import Spinner
import pickle

# this python script takes in all agent-people from ASpace and outputs that same list (or that list limited to a specific name-source) with all names corrected to have inverted name order (as specified in DACS)

############################################################

def get_item(location):
    return requests.get(backendURL + location,  headers=headers).json()

def invert_names(name_list):
    # things to update = title, names(name_order, primary_name, rest_of_name,sort_name),
    # display_name(name_order, primary_name, rest_of_name, sort_name)
    inverted = []
    for i in name_list:
        namesplit = [n for n in i['title'].split(' ') if n != '']
        if len(namesplit) == 1:
            i['names'][0]['name_order'] = 'inverted'
            i['display_name']['name_order'] = 'inverted'
            inverted.append(i)
        else:
            newtitle = namesplit[-1]+', '+' '.join(namesplit[0:-1])
            last_name = namesplit[-1]
            rest = ' '.join(namesplit[0:-1])
            i['names'][0]['name_order'] = 'inverted'
            i['names'][0]['primary_name'] = last_name
            i['names'][0]['rest_of_name'] = rest
            i['names'][0]['sort_name'] = newtitle
            i['display_name']['name_order'] = 'inverted'
            i['display_name']['primary_name'] = last_name
            i['display_name']['rest_of_name'] = rest
            i['display_name']['sort_name'] = newtitle
            inverted.append(i)
    return inverted

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)

############################################################

# connect to the AS API and the UW Ethno Archives repository
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

print('loading all agent-people IDs...')
agent_ids = get_item('/agents/people?all_ids=True')

spinner = Spinner('loading all agent-people records...')
state = 'loading'

all_ppl = []
while state != 'FINISHED':
    for a in agent_ids:
        all_ppl.append(get_item('/agents/people/'+str(a)))
        spinner.next()
    state = 'FINISHED'

print(' successfully downloaded '+str(len(all_ppl))+' records')

limit = input('would you like to limit the agent-people list by name source? (y/n) ')

if limit == 'n':
    updates = invert_names(all_ppl)
elif limit == 'y':
    source_limit = input('enter the exact name of the name-source to focus on (e.g. local): ')
    ppl = [i for i in all_ppl if i['names'][0]['source'] == source_limit]
    print('now focusing on '+str(len(ppl))+' records')
    updates = invert_names(ppl)
else:
    print('Invalid limit type given, please try again.')
    updates = []

if updates != []:
    output = input("enter the path and name of the data file to store your saved agents in (e.g. ./data/inverted_agents.txt): ")
    write_pickle(updates, output)
    print('data saved!')
else:
    print('nothing was updated...try again')
