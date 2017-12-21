#!/usr/bin/env python

import json
import requests
from progress.spinner import Spinner
import pickle

# this python script downloads all ethnomusicology resources from the ASpace API 
# then, it locates the ead_location in each remotely updated resource record
# matches remotely updated resources to downloaded resource records by id_0
# then updates the ead_location in each matched resource record
# and uploads them to ASpace

############################################################

def get_item(location):
    return requests.get(backendURL + location,  headers=headers).json()

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def post_item(item, location):
    jsonData = json.dumps(item)
    postItem = requests.post(backendURL + location,  headers=headers, data=jsonData)
    return postItem.json()

def import_data(item_list):
    spinner = Spinner('Updating items...')
    state = 'loading'
    while state != 'FINISHED':
        for idx,item in enumerate(item_list):
            posted = post_item(item, item['uri'])
            spinner.next()
            if 'error' in posted.keys():
                print((' List item number: '+str(idx)+' was not posted! See error message. ',posted))
                print('Item uri: '+item['uri'])
                next_item = idx+1
                print('Next list item to post will be: '+item_list[next_item]['uri'])
                break
        state = 'FINISHED'
    print('Import complete.')

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
# id2 = test resource; id4 = barton; control for future additions
eth_ids = [i for i in eth_ids if i in list(range(5,2998))]

spinner = Spinner('loading all ethnomusicology resources...')
state = 'loading'

# get each ethno resource by id, create a list of each resource (Note: takes several minutes)
eth_list = []
while state != 'FINISHED':
    for a in eth_ids:
        eth_list.append(get_item('/repositories/2/resources/'+str(a)))
        spinner.next()
    state = 'FINISHED'

print(' successfully downloaded '+str(len(eth_list))+' resources')

############################################################

data_file = input("Enter the path to the downloaded data file containing the updated records (e.g. ./data/updated_resources.txt): ")

updated_resources = load_pickled(data_file)

output_updates = []
for i in eth_list:
    if i['id_0'] in updated_resources:
        i['ead_location'] = updated_resources[i['id_0']]
        output_updates.append(i)

print(str(len(output_updates))+' records will be updated on ArchivesSpace with an ARK code from Archives West.')

############################################################

import_option = input("Updating records on ASpace will overwrite existing data. Are you sure you'd like to continue? (y/n) ")

if import_option == 'y':

    ###### connect to the AS API again in case of time out ######
    connectASpace = requests.post('http://localhost:8089/users/admin/login', data = {"password":password})

    if connectASpace.status_code == 200:
        print("Successfully re-connected to the ASpace backend!")
        sessionID = connectASpace.json()["session"]
        headers = {'X-ArchivesSpace-Session': sessionID}

        shorten = input("Does the data list need to be truncated (are you re-importing a failed import job from where you left off)? (y/n) ")

        if shorten == 'y':
            index = int(input("Enter the index (item number) of the item to start importing from: "))
            short_list = output_updates[index:]
            import_data(short_list)
        else:
            import_data(output_updates)
    else:
        print(connectASpace.status_code)
