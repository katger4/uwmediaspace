#!/usr/bin/env python

import json
import requests
from progress.spinner import Spinner
import pickle

# this python script takes in all agent-people or corporate entities from ASpace and outputs a list of agent records to use in other scripts

############################################################

def get_item(location):
    return requests.get(backendURL + location,  headers=headers).json()

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

agent_type = input("Enter the type of agents to download (options are: people or corporate): ")

if agent_type == 'people':
    print('loading all agent-people IDs...')
    agent_ids = get_item('/agents/people?all_ids=True')

    spinner = Spinner('loading all agent-people records...')
    state = 'loading'

    all_agents = []
    while state != 'FINISHED':
        for a in agent_ids:
            all_agents.append(get_item('/agents/people/'+str(a)))
            spinner.next()
        state = 'FINISHED'

    print(' successfully downloaded '+str(len(all_agents))+' records')

elif agent_type == 'corporate':
    print('loading all agent-corporate-entities IDs...')
    corp_ids = get_item('/agents/corporate_entities?all_ids=True')

    spinner = Spinner('loading all agent-corporate entities records...')
    state = 'loading'

    all_agents = []
    while state != 'FINISHED':
        for a in corp_ids:
            all_agents.append(get_item('/agents/corporate_entities/'+str(a)))
            spinner.next()
        state = 'FINISHED'

    print(' successfully downloaded '+str(len(all_agents))+' records')

else:
    print('Invalid agent type given, please try again.')
    all_agents = []

if all_agents != []:
    output = input("enter the path and name of the data file to store your saved agents in (e.g. ./data/people.txt): ")
    write_pickle(all_agents, output)
    print('data saved!')
else:
    print('nothing was downloaded...try again')
