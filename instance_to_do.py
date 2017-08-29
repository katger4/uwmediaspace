#!/usr/bin/env python

import json
import requests
from progress.spinner import Spinner
import pickle

# this python script takes extracts erroneous container information from archival objects in a series in an ASpace resource and converts them to digital objects for import to ASpace, maintaining links to the original records

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

# get each ethno resource by id, create a list of each resource (Note: takes several minutes)
mr_aos = []
while state != 'FINISHED':
    for a in mr_ids:
        mr_aos.append(get_item('/repositories/'+repository+'/archival_objects/'+str(a)))
        spinner.next()
    state = 'FINISHED'

print(' successfully downloaded '+str(len(mr_aos))+' archival objects')

# extract filenames from instance list
# create digital object records, creating a dict of DO-id:URI
# match each DO to its AO by ID
# remove container file link
# add DO link
# create a dict of (filename,reel): [uris] tuples
new_title = input("Create new digital object title? (y/n) ")
if new_title == 'y':
    do_title = input("Enter the new digital object title prefix (e.g. Ryan Reel): ")


dos = {}
for i in mr_aos:
    if 'indicator_3' in i['instances'][0]['sub_container']:
        filename = i['instances'][0]['sub_container']['indicator_3']

        if do_title:
            title = do_title+' '+i['instances'][0]['sub_container']['indicator_2']
        else:
            title = i['title']

        key = (filename, title)
        if key not in dos:
            dos[key] = [{'ref': i['uri']}]
        else:
            dos[key].append({'ref': i['uri']})

digital_objects = []
for key,uris in dos.items():
    digital_objects.append({'digital_object_id': key[0],
                            'jsonmodel_type': 'digital_object',
                            'linked_instances': uris,
                            'repository': {'ref': '/repositories/'+repository},
                            'title': key[1]})

digital_objects = sorted(digital_objects, key=lambda k: k['title']) 

print('successfully created '+str(len(digital_objects))+' digital objects!')

output = input("enter the path and name of the data file to store your saved digital objects in (e.g. ./data/digi_objects.txt): ")
write_pickle(digital_objects, output)
print('data saved!')
