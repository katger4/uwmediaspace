#!/usr/bin/env python

import json
import requests
from progress.spinner import Spinner
from progress.spinner import MoonSpinner
import pickle

# this python script downloads the archival objects of each of the original 1499 ethnomusicology archive collections and outputs a list of archival objects

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

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

ethno = load_pickled('./data/ethno.txt')


spinner = MoonSpinner('loading the resource trees...')
state = 'loading'

ao_ids = []
while state != 'FINISHED':
    for i in ethno:
        if 'Crocodile' not in i['title']:
            tree = get_item(i['uri']+'/tree')
            if tree['children'] != []:
                for child in tree['children']:
                    ao_ids.append(child['id'])
                    spinner.next()
            else:
                spinner.next()
        else:
            spinner.next()
    state = 'FINISHED'

spinner = Spinner('\nloading all archival objects...')
state = 'loading'

# get each archival object by id, create a list of each AO (Note: takes several minutes)
aos = []
while state != 'FINISHED':
    for a in ao_ids:
        aos.append(get_item('/repositories/2/archival_objects/'+str(a)))
        spinner.next()
    state = 'FINISHED'

print(' successfully downloaded '+str(len(aos))+' archival objects')

output = input("enter the path and name of the data file to store your saved archival objects in (e.g. ./data/ethno_aos.txt): ")
write_pickle(aos, output)
print('data saved!')

