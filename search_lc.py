#!/usr/bin/env python

import csv
import requests
from bs4 import BeautifulSoup
from progress.spinner import Spinner
from fuzzywuzzy import fuzz
import unicodedata
import regex
import re

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
	with open(output, 'w', encoding='utf-8-sig') as out_file:
		writer = csv.writer(out_file, delimiter='\t')
		for name,lc in data:
			writer.writerow((name,lc))

def create_lc_address(name):
	name_list = name.split(' ')
	search_name = '+'.join(name_list)
	lc_address = "http://id.loc.gov/search/?q="+search_name+"&q=cs%3Ahttp%3A%2F%2Fid.loc.gov%2Fauthorities%2Fnames"
	return lc_address

def prep_lc_name(lc_name):
	# remove anything in parenthesis from lc name for comparison purposes
	lc = re.sub(r'\([^)]*\)', '', lc_name).strip() 
	# https://stackoverflow.com/questions/3833791/python-regex-to-convert-non-ascii-characters-in-a-string-to-closest-ascii-equiva
	# convert foregin chars to closest matching ascii char for fuzzy comparison
	# all names lack special characters
	lc_test = regex.sub(r"\p{Mn}", "", unicodedata.normalize("NFKD", lc))
	# also remove digits for comparison purposes
	lc_test = re.sub(r'\d+', '', lc_test).strip()
	return lc_test

def search_lc(name, lc_address):
	# search LoC for that name
	response = requests.get(lc_address).content
	# parse search results using bs4
	soup = BeautifulSoup(response, 'lxml')
	table = soup.find('table', {"class" : "id-std"})
	if table != None:
		headers = [header.text for header in table.find_all('th',{'scope' :'col'})]
		rows = [{headers[i]: cell.text for i, cell in enumerate(row.findAll("td"))} for row in table.select("tbody tr")]
		# now do fuzzy matching
		potential = None
		for row in rows:
			lc_test = prep_lc_name(row['Label'])
			# get fuzzy match ratio
			ratio = fuzz.token_sort_ratio(lc_test, name)
			# print(name, row['Label'], ratio)
			if ratio >= 60 :
				potential = (name, row['Label'])
				break

		return potential


############################################################

# filename = input("Enter filename of the list of names to search: ")
# unlikely = load_csv(filename)
unlikely = load_csv('./data/_unlikely.tsv')
print(len(unlikely))

# lc_address = create_lc_address('bat for lashes')
# print(lc_address)
# new_match = search_lc('bat for lashes', lc_address)
# print(new_match)

spinner = Spinner('searching name authority files...')
state = 'loading'

found_names = []
not_found = []

while state != 'FINISHED':
	for name in unlikely:
		name = name.replace('UW ', 'University of Washington ')
		lc_address = create_lc_address(name)
		new_match = search_lc(name, lc_address)
		if new_match != None:
			found_names.append(new_match)
			spinner.next()
		else:
			not_found.append((name, 'no match'))
			spinner.next()
	state = 'FINISHED'

print('\nfound '+str(len(found_names))+' potential matches')
print('but '+str(len(not_found))+' were not found')

write_tsv(sorted(found_names), './data/found_names.tsv')
write_tsv(sorted(not_found), './data/not_found.tsv')

