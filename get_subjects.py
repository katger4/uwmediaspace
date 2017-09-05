#!/usr/bin/env python

import json
import requests
from progress.spinner import Spinner
import pickle

# this python script takes in all subjects from ASpace and outputs a list of records to use in other scripts

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

print('loading all agent-people IDs...')
subject_ids = get_item('/subjects?all_ids=True')

spinner = Spinner('loading all subjects...')
state = 'loading'

all_subs = []
while state != 'FINISHED':
    for s in subject_ids:
        all_subs.append(get_item('/subjects/'+str(s)))
        spinner.next()
    state = 'FINISHED'

print(' successfully downloaded '+str(len(all_subs))+' records')

if all_subs != []:
    output = input("enter the path and name of the data file to store your saved agents in (e.g. ./data/subjects.txt): ")
    write_pickle(all_subs, output)
    print('data saved!')
else:
    print('nothing was downloaded...try again')
