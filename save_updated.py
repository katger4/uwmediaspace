#!/usr/bin/env python

import pickle
from datetime import datetime

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)

############################################################

# get the string of the last resource update
last_update = input("Enter the datetime string of the last update: ")

# convert to a datetime object
last_update_dt = datetime.strptime(last_update, '%Y-%m-%dT%H:%M:%SZ')

filename = input("Enter the path to the data file containing the downloaded records (e.g. ./data/ethno.txt): ")

resources = load_pickled(filename)

updated = []
for i in resources:
	update_dt = datetime.strptime(i['user_mtime'], '%Y-%m-%dT%H:%M:%SZ')
	if update_dt > last_update_dt:
		updated.append(i)

print(str(len(updated))+' resources have been modified this session. ')

output_data = {i['id_0']:i['ead_location'] for i in updated}
output_path = input("enter the path and name of the data file to store your saved data in (e.g. ./data/updated_resources.txt): ")
write_pickle(output_data, output_path)
print('data saved!')

