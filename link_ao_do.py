#!/usr/bin/env python

import pickle

# this python script links digital objects and archival objects by id (temporarily stored in the instance field), then outputs a list of archival objects to update

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)

def create_link(do_id):
	return {'digital_object': {'ref': do_uri[do_id]}, 'instance_type': 'digital_object', 'jsonmodel_type': 'instance'}

############################################################

# load dos
dos = load_pickled('./data/digi_objects.txt')
# load aos
aos = load_pickled('./data/mr_aos.txt')

# create a dict of DO id:uri
do_uri = {i['digital_object_id']: i['uri'] for i in dos}

updates = []
# link aos to dos by id, remove container instance, add do instance
for i in aos:
	if 'indicator_3' in i['instances'][0]['sub_container']:
		do_id = i['instances'][0]['sub_container']['indicator_3']
		if do_id in do_uri:
			i['instances'].append(create_link(do_id))
			i['instances'][0]['sub_container'].pop('indicator_3')
			i['instances'][0]['sub_container'].pop('type_3')
			updates.append(i)

print('successfully linked '+str(len(updates))+' AOs to DOs')

output = input("enter the path and name of the data file to store your saved archival objects in (e.g. ./data/updates.txt): ")
write_pickle(updates, output)
print('data saved!')
