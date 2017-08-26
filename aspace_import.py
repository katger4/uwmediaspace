#!/usr/bin/env python

import json
import requests
import pickle

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def post_item(item, location):
    jsonData = json.dumps(item)
    postItem = requests.post(backendURL + location,  headers=headers, data=jsonData)
    return postItem.json()

filename = input("Enter the path to the data file containing the structured list of items for import (usually the output of another script e.g. ./data/subjects.txt): ")

item_list = load_pickled(filename)

import_type = input("Enter the type of items to be imported to ASpace (options are: subjects, people, corporate_entites, or records): ")

if import_type == 'subjects':
	location = '/subjects'
elif import_type == 'people':
	location = '/agents/people'
elif import_type == 'corporate_entites':
	location = '/agents/corporate_entities'
elif import_type == 'records':
	location = item['uri']
else:
	print('Invalid item type given, please try again.')

# connect to the AS API and the UW Ethno Archives repository
backendURL = 'http://localhost:8089'

password = input("Enter the administrative password: ")

#inital request for session
connectASpace = requests.post('http://localhost:8089/users/admin/login', data = {"password":password})

if connectASpace.status_code == 200:
    print("Connection Successful!")
    sessionID = connectASpace.json()["session"]
    headers = {'X-ArchivesSpace-Session': sessionID}
else:
    print(connectASpace.status_code)

print('Importing items...')
for idx,item in enumerate(item_list):
    posted = post_item(item, location)
    if 'error' in posted.keys():
        print(('List item number: '+str(idx)+' was not posted! See error message. ',posted))
        next_item = idx+1
        print('Next list item to post will be '+item_list[next_item])
        break
print('Import complete.')