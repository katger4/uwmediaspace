#!/usr/bin/env python

import csv
import requests
from bs4 import BeautifulSoup
from progress.spinner import Spinner

# this python script takes a list of name-lcnaf tuples (output from the 'fuzz_names.py' script) and queries the lcnaf database directly for those names that did not match in the viaf.py process by appending likely terms to the search name (e.g. ' (musical group)' or ' (rock group)')

############################################################

def load_csv(filename):
	with open(filename, 'r', encoding='utf-8-sig') as file:
		# create a csv-reader object
		reader = csv.reader(file, delimiter='\t')
		# loop through each row in the csv-reader object
		# create a dict of name:lcnaf
		data = {row[0]: row[1] for row in reader}
	return data

def write_tsv(data, output):
	with open(output, 'w') as out_file:
		writer = csv.writer(out_file, delimiter='\t')
		for name,lc in data:
			writer.writerow((name,lc))

def search_lc(name, addition):
	# create the LoC address
	name_list = name.split(' ')
	search_name = '+'.join(name_list)
	lc_address = "http://id.loc.gov/search/?q="+search_name+"+%28"+addition+"+group%29&q=cs%3Ahttp%3A%2F%2Fid.loc.gov%2Fauthorities%2Fnames"
	# search LoC for that name
	response = requests.get(lc_address).content
	# parse search results using bs4
	soup = BeautifulSoup(response, 'lxml')
	table = soup.find('table', {"class" : "id-std"})
	headers = [header.text for header in table.find_all('th',{'scope' :'col'})]
	rows = [{headers[i]: cell.text for i, cell in enumerate(row.findAll("td"))} for row in table.select("tbody tr")]
	# create match name variable to check table values against
	match_name = name.lower()+' ('+addition+' group)'
	for row in rows:
		if row['Label'].lower() == match_name:
			return (name, row['Label'])

############################################################

unlikely = load_csv('./data/unlikely.tsv')
print(len(unlikely))

spinner = Spinner('searching name authority files...')
state = 'loading'

found_names = []

name_addition = input("Enter the type of name to search for (e.g. musical or rock): ")

while state != 'FINISHED':
	for name in unlikely:
		new_match = search_lc(name[0], name_addition)
		if new_match != None:
			found_names.append(new_match)
			spinner.next()
		else:
			spinner.next()
	state = 'FINISHED'

print('\n'+str(len(found_names)))

write_tsv(found_names, './data/found_names.tsv')

