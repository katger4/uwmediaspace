#!/usr/bin/env python

import csv
import requests
from bs4 import BeautifulSoup
from progress.spinner import Spinner
from fuzzywuzzy import fuzz

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

def create_lc_address(name, name_addition):
	name_list = name.split(' ')
	search_name = '+'.join(name_list)

	if name_addition == '':
		lc_address = "http://id.loc.gov/search/?q="+search_name+"&q=cs%3Ahttp%3A%2F%2Fid.loc.gov%2Fauthorities%2Fnames"
	else:
		lc_address = "http://id.loc.gov/search/?q="+search_name+"+%28"+name_addition+"+group%29&q=cs%3Ahttp%3A%2F%2Fid.loc.gov%2Fauthorities%2Fnames"
	return lc_address

def search_lc(name, lc_address):
	# search LoC for that name
	response = requests.get(lc_address).content
	# parse search results using bs4
	soup = BeautifulSoup(response, 'lxml')
	table = soup.find('table', {"class" : "id-std"})
	if table != None:
		headers = [header.text for header in table.find_all('th',{'scope' :'col'})]
		rows = [{headers[i]: cell.text for i, cell in enumerate(row.findAll("td"))} for row in table.select("tbody tr")]
		# create match name variable to check table values against
		if name_addition != '':
			match_name = name.lower()+' ('+name_addition+' group)'
			for row in rows:
				if row['Label'].lower() == match_name:
					return (name, row['Label'])
		else:
			match_name = name.lower()
			potential = None
			for row in rows:
				ratio = fuzz.token_sort_ratio(row['Label'].lower(), match_name)
				if ratio >= 70 :
					potential = (name, row['Label'])
					break
			return potential


############################################################

# filename = input("Enter filename of the list of names to search: ")
# unlikely = load_csv(filename)
unlikely = load_csv('./data/noID.csv')
print(len(unlikely))

# name_addition = input("Enter the type of name to search for (e.g. musical or rock): ")

name_addition = ''

# lc_address = create_lc_address('bat for lashes', name_addition)
# print(lc_address)
# new_match = search_lc('bat for lashes', lc_address)
# print(new_match)

spinner = Spinner('searching name authority files...')
state = 'loading'

found_names = []
while state != 'FINISHED':
	for name in unlikely:
		lc_address = create_lc_address(name, name_addition)
		new_match = search_lc(name, lc_address)
		if new_match != None:
			found_names.append(new_match)
			spinner.next()
		else:
			spinner.next()
	state = 'FINISHED'

print('\nfound '+str(len(found_names))+' potential matches')

write_tsv(found_names, './data/found_names.tsv')

