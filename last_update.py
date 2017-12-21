#!/usr/bin/env python

import json
import requests
from progress.spinner import Spinner
from datetime import datetime

# this python script downloads all ethnomusicology resources from the ASpace API , then prints out the time of the last update

############################################################

def get_item(location):
    return requests.get(backendURL + location,  headers=headers).json()

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

by_id = input('Find update time by resource id (y/n)? ')

if by_id == 'n':
    
    latest = datetime.strptime('0001-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    
    for i in eth_list:
        raw = i['user_mtime'].replace('T', ' ').replace('Z', '')
        datetime_object = datetime.strptime(raw, '%Y-%m-%d %H:%M:%S')
        if datetime_object > latest:
            latest = datetime_object
    
    print('Last resource was updated at: '+latest.strftime('%Y-%m-%dT%H:%M:%SZ'))

elif by_id == 'y':
    
    id_0 = input('Enter the id of the resource to check its last update time: ')
    
    for i in eth_list:
        if i['id_0'] == id_0:
            print('Resource '+id_0+' was updated at: '+i['user_mtime'])
