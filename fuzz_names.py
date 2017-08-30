#!/usr/bin/env python

import csv
from fuzzywuzzy import fuzz

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

############################################################

lcnaf = load_csv('./data/lcnaf.tsv')
print(len(lcnaf))

# escape_term = input('Enter any phrase to remove from the lc term (e.g. (Musical group): ')
escape_term = ' (Musical group)'
escape_term2 = ' (Rock group)'

likely = []
unlikely = []
for name,lc in list(lcnaf.items()):
	name_test = name.replace('The', '')
	lc_test = lc.replace(escape_term,'').replace(escape_term2,'')
	#print((name_test, lc_test, fuzz.token_sort_ratio(name_test, lc_test)))
	ratio = fuzz.token_sort_ratio(name_test, lc_test)
	if ratio >= 80:
		likely.append((name,lc))
	else:
		unlikely.append((name,lc))

print(len(likely))
print(len(unlikely))

write_tsv(likely, './data/lcnaf_fuzz.tsv')
write_tsv(unlikely, './data/unlikely.tsv')
