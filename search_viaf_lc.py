#!/usr/bin/env python

import pickle
from lxml import etree
import requests
from bs4 import BeautifulSoup
from progress.spinner import Spinner
import csv
from fuzzywuzzy import fuzz
import re
import unicodedata
import regex

# this python script uses VIAF and LCNAF querying functions modified from http://archival-integration.blogspot.com/2015/07/order-from-chaos-reconciling-local-data.html to reconcile stored agent names with authority files

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def retrieve_viaf_search_results(search_index, search_term):
    search_url_template = 'http://viaf.org/viaf/search/viaf?query=local.'+search_index+'+all+"'+search_term+'"+and+local.sources+any+"lc"&sortKeys=holdingscount&httpAccept=application/xml'
    response = requests.get(search_url_template)
    return response.content


def get_lc_auth_from_viaf_data(response):
    lc_auth = ""
    # parse the returned xml into an lxml etree
    tree = etree.fromstring(response)
    # extract a list of the VIAF search result nodes using an xpath query
    results = tree.xpath("//*[local-name()='record']")
    # if there are any search results, grab the first one
    if len(results) > 0:
        primary_result = results[0]
        # Extract all auth sources for this search result
        sources = primary_result.xpath("//*[local-name()='mainHeadingEl']/*[local-name()='id']")
        # There are usually a number of sources, but we only want the LoC
        for source in sources:
            if "LC|" in source.text:
                # needs some formatting to extract the number only
                lc_auth = source.text.split("|")[1].replace(" ", "")
                break
    return lc_auth

def get_lc_term_name(lc_auth_number):
    # create the LoC address
    lc_address = "http://id.loc.gov/authorities/names/"+lc_auth_number
    # get the page headers for that address if it exists
    response = requests.get(lc_address).headers
    # use the preferred name (part of the headers)
    lc_name = response['X-PrefLabel']
    # add this decode/encode step to properly view foreign characters
    return lc_name.encode('latin-1').decode()

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

def create_lc_address(name, agent_type):
    name_list = name.split(' ')
    search_name = '+'.join(name_list)
    if agent_type == 'corporate' or agent_type == 'people':
        lc_address = "http://id.loc.gov/search/?q="+search_name+"&q=cs%3Ahttp%3A%2F%2Fid.loc.gov%2Fauthorities%2Fnames"
    elif agent_type == 'geographic':
        lc_address = "http://id.loc.gov/search/?q="+search_name+"&q=cs%3Ahttp%3A%2F%2Fid.loc.gov%2Fvocabulary%2FgeographicAreas"
    else:
        lc_address = "http://id.loc.gov/search/?q="+search_name+"&q=cs%3Ahttp%3A%2F%2Fid.loc.gov%2Fauthorities%2Fsubjects"
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
        # now do fuzzy matching
        potential = None
        for row in rows:
            lc_test = prep_lc_name(row['Label'])
            # get fuzzy match ratio
            ratio = fuzz.token_sort_ratio(lc_test, name)
            # print(name, row['Label'], ratio)
            if ratio >= 80 :
                potential = (name, row['Label'])
                break

        return potential

def write_tsv(data, output):
    with open(output, 'w', encoding='utf-8-sig') as out_file:
        writer = csv.writer(out_file, delimiter='\t')
        for name,lc in data:
            writer.writerow((name,lc))

############################################################

# load agents/subjects
filename = input("Enter the path to the data file containing the downloaded records (e.g. ./data/people.txt): ")

agents = load_pickled(filename)

agent_type = input('Enter the type of records (people, corporate, topical or geographic): ')
if agent_type == 'corporate':
    search_index = 'corporateNames'
elif agent_type == 'people':
    search_index = 'personalNames'
elif agent_type == 'geographic':
   search_index = 'geographicNames'
# search_index = 'corporateNames'

source_limit = input('enter the exact name of the name-source to focus on (e.g. local): ')

if agent_type != 'geographic' and agent_type != 'topical':
    agents = [i for i in agents if i['display_name'].get('source') == source_limit]
else:
    agents = [i for i in agents if i.get('source') == source_limit]
# agents = ['Cicek, Ali Ekber', 'Carter, Bo']
print('will search for '+str(len(agents))+' possible LoC terms')

if agent_type != 'topical':
    spinner = Spinner('searching LoC authority files...')
    state = 'loading'

    noID = []
    matches = {}

    while state != 'FINISHED':
        for agent in agents:
            if agent_type != 'geographic':
                search_term = agent['display_name']['sort_name']
            else:
                search_term = agent['title']
            response = retrieve_viaf_search_results(search_index, search_term)
            lc_auth_number = get_lc_auth_from_viaf_data(response)
            if lc_auth_number != '':
                lc_name = get_lc_term_name(lc_auth_number)
                if lc_name != None:
                    matches[search_term] = lc_name
                    spinner.next()
                else:
                    spinner.next()
            else:
                noID.append((search_term, 'not found'))
                spinner.next()
        state = 'FINISHED'

    likely = []
    unlikely = []

    # fuzzy matching to remove unlikely matches
    if agent_type == 'corporate':
        for name,lc in list(matches.items()):
            # remove extra 'The' (for band name comparison mostly)
            # convert UW to University of Washington 
            name_test = name.replace('The', '').replace('UW ', 'University of Washington ')
            lc_test = prep_lc_name(lc)
            ratio = fuzz.token_sort_ratio(name_test, lc_test)
            if ratio >= 75:
                likely.append((name,lc))
            else:
                unlikely.append((name,lc))
                
    elif agent_type == 'people':
        for name,lc in list(matches.items()):
            lc_test = prep_lc_name(lc)
            ratio = fuzz.token_sort_ratio(name, lc_test)
            # print((name, lc, ratio))
            if ratio >= 80:
                likely.append((name,lc))
            else:
                unlikely.append((name,lc))

    elif agent_type == 'geographic':
        for name,lc in list(matches.items()):
            ratio = fuzz.token_sort_ratio(name, lc)
            # print((name, lc, ratio))
            if ratio >= 80:
                likely.append((name,lc))
            else:
                unlikely.append((name,lc))

    print('\nfound '+str(len(likely))+' likely matches')
    print('and '+str(len(unlikely))+' unlikely matches')
    print(str(len(noID))+' names were not found in VIAF')

if agent_type != 'topical':
    unlikely = sorted(unlikely)+sorted(noID)
else:
    unlikely = [(s['title'],'nothing') for s in agents]
    likely = None

# create a dict of name:lcnaf
unlikely_dict = {name:lc for name,lc in unlikely}

print('will search for '+str(len(unlikely_dict))+' terms in LoC directly')

spinner = Spinner('searching LoC...')
state = 'loading'

found_names = []
not_found = []

while state != 'FINISHED':
    for name in unlikely_dict:
        name = name.replace('UW ', 'University of Washington ')
        lc_address = create_lc_address(name, agent_type)
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

write_tsv(sorted(found_names), './data/lc_found_names.tsv')
write_tsv(sorted(not_found), './data/lc_not_found.tsv')

if likely:
    write_tsv(sorted(likely), './data/likely.tsv')

print('data saved for quality control!')

