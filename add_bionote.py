#!/usr/bin/env python

import pickle

# this python script takes in a list of resources from an ASpace repo, filters that list by a specified creator, then adds a biographical note or a historical note (from a text file) to each resource 

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def open_txt(filename):
	with open(filename, "r") as f:
		text_list = ['<p>'+line.strip()+'</p>' for line in f if line != '']
		text = ''.join(text_list)
		return text

def write_pickle(item, filename):
    with open(filename, "wb") as fp:   #Pickling
        pickle.dump(item, fp)

############################################################

# load text
filename_t = input('enter the path to the text file containing the biographical/historical note (e.g. ./data/note.txt): ')
content = open_txt(filename_t)
print('Formatted note text to add:\n'+content)

# # load resources
filename_r = input('enter the path to the saved list of resources (e.g. ./data/resources.txt): ')
resources = load_pickled(filename_r)

creator_type = input('enter the type of creator to limit the resource list by (person or corporate): ')
creator_id = input('enter the ASpace ID of the creator to limit the resource list by (just the numeric value - located at the end of the url for each agent on ASpace): ')

if creator_type == 'person':
	agent_ref = '/agents/people/'+creator_id
	note_label = 'Biographical Note'
elif creator_type == 'corporate':
	agent_ref = '/agents/corporate_entities/'+creator_id
	note_label = 'Historical Note'
else:
	print('invalid creator type provided.')

bioghist = {'jsonmodel_type': 'note_multipart',
			'publish': False,
			'label': note_label,
			'subnotes': [{'content': content,
						  'jsonmodel_type': 'note_text',
						  'publish': False}],
			'type': 'bioghist'}

# limit resources by creator
resources_to_edit = [i for i in resources if any(a.get('ref') == agent_ref for a in i['linked_agents'])]

updates = []
for i in resources_to_edit:
	# resources on AW will have an ARK ID
	if '[Insert ARK ID]' in i['ead_location']:
		# check for existing bioghist content
		if any(n.get('type') == 'bioghist' for n in i['notes']):
			proceed = input('the resource '+i['id_0']+': '+i['title']+' already has a biographical/historical note. do you want to overrwrite that note with new content? (y/n) ')
			if proceed == 'y':
				i['notes'] = [n for n in i['notes'] if n['type'] != 'bioghist']
				i['notes'].append(bioghist)
				updates.append(i)
		if not any(n.get('type') == 'bioghist' for n in i['notes']):
			i['notes'].append(bioghist)
			updates.append(i)

if updates != []:
	print('added biographical notes to '+str(len(updates))+' resources')
	output = input("enter the path and name of the data file to store your data file in (e.g. ./data/updates.txt): ")
	write_pickle(updates, output)
	print('data saved!')
else:
	print('no data to save')

