#!/usr/bin/env python

import json
import requests
from progress.spinner import Spinner
import pickle

# this python script takes in all agent-people from ASpace and outputs that same list (or that list limited to a specific name-source) with all names corrected to have inverted name order (as specified in DACS)

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

print('loading all ethnomusicology resource IDs...')
# get the ids of each ethno resource
eth_ids = get_item('/repositories/2/resources?all_ids=True')
# id2 = test resource; id4 = barton
eth_ids = [i for i in eth_ids if i not in [2,4]]

spinner = Spinner('loading all ethnomusicology resources...')
state = 'loading'

# get each ethno resource by id, create a list of each resource (Note: takes several minutes)
eth_list = []
while state != 'FINISHED':
    for a in eth_ids:
        eth_list.append(get_item('/repositories/2/resources/'+str(a)))
        spinner.next()
    state = 'FINISHED'

print(' successfully downloaded '+str(len(all_ppl))+' resources')

output = input("enter the path and name of the data file to store your saved agents in (e.g. ./data/ethno.txt): ")
write_pickle(eth_list, output)
print('data saved!')
