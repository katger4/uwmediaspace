#!/usr/bin/env python

import json
import requests
import pickle
from progress.spinner import Spinner

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def post_item(item, location):
    jsonData = json.dumps(item)
    postItem = requests.post(backendURL + location,  headers=headers, data=jsonData)
    return postItem.json()

def import_data(item_list):
    spinner = Spinner('Importing items...')
    state = 'loading'
    while state != 'FINISHED':
        for idx,item in enumerate(item_list):
            posted = post_item(item, item['uri'])
            spinner.next()
            if 'error' in posted.keys():
                print(('List item number: '+str(idx)+' was not posted! See error message. ',posted))
                next_item = idx+1
                print('Next list item to post will be '+item_list[next_item])
                break
        state = 'FINISHED'
    print('Import complete.')

############################################################

filename = input("Enter the path to the data file containing the structured list of records to update on ASpace (usually the output of another script e.g. ./data/inverted_agents.txt): ")

item_list = load_pickled(filename)

import_option = input("Updating records on ASpace will overwrite existing data. Are you sure you'd like to continue? (y/n) ")

if import_option == 'y':

    ###### connect to the AS API ######
    backendURL = 'http://localhost:8089'

    password = input("Enter the administrative password: ")

    #inital request for session
    connectASpace = requests.post('http://localhost:8089/users/admin/login', data = {"password":password})

    if connectASpace.status_code == 200:
        print("Successfully connected to the ASpace backend!")
        sessionID = connectASpace.json()["session"]
        headers = {'X-ArchivesSpace-Session': sessionID}

        shorten = input("Does the data list need to be truncated (are you re-importing a failed import job from where you left off)? (y/n) ")

        if shorten == 'y':
            index = int(input("Enter the index (item number) of the item to start importing from: "))
            short_list = item_list[index:]
            import_data(short_list)
        else:
            import_data(item_list)
    else:
        print(connectASpace.status_code)

