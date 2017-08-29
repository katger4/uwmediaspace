#!/usr/bin/env python

import json
import requests
from progress.spinner import Spinner
import pickle

# this python script downloads the digital objects of a given repo for use in other scripts

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

repository = input("Enter the repository id: ")

# get the ids of each archival object in the series
do_ids = get_item('/repositories/'+repository+'/digital_objects?all_ids=true')

spinner = Spinner('loading all digital objects...')
state = 'loading'

# get each digital object by id, create a list of each DO (Note: takes several minutes)
dos = []
while state != 'FINISHED':
    for a in do_ids:
        dos.append(get_item('/repositories/'+repository+'/digital_objects/'+str(a)))
        spinner.next()
    state = 'FINISHED'

print(' successfully downloaded '+str(len(dos))+' digital objects')

output = input("enter the path and name of the data file to store your saved digital objects in (e.g. ./data/digi_objects.txt): ")
write_pickle(dos, output)
print('data saved!')
