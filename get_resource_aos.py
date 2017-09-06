#!/usr/bin/env python

import json
import requests
from progress.spinner import Spinner
import pickle

# this python script downloads the archival objects of a given resource-series for use in other scripts

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
resource = input("Enter the resource id: ")
series = input("Enter the series title: ")

print('loading the resource tree...')
tree = get_item('/repositories/'+repository+'/resources/'+resource+'/tree')
# get the index of the series
for idx,i in enumerate(tree['children']):
    if series in i['title']:
        seriesindex = idx

# get the ids of each archival object in the series
mr_ids = [i['id'] for i in tree['children'][seriesindex]['children']]

spinner = Spinner('loading all archival objects...')
state = 'loading'

# get each archival object by id, create a list of each AO (Note: takes several minutes)
mr_aos = []
while state != 'FINISHED':
    for a in mr_ids:
        mr_aos.append(get_item('/repositories/'+repository+'/archival_objects/'+str(a)))
        spinner.next()
    state = 'FINISHED'

print(' successfully downloaded '+str(len(mr_aos))+' archival objects')

output = input("enter the path and name of the data file to store your saved archival objects in (e.g. ./data/aos.txt): ")
write_pickle(mr_aos, output)
print('data saved!')



