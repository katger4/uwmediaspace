#!/usr/bin/env python

import pickle
from lxml import etree
import requests
from progress.spinner import Spinner
import timeit

# this python script uses VIAF and LCNAF querying functions modified from http://archival-integration.blogspot.com/2015/07/order-from-chaos-reconciling-local-data.html to reconcile stored agent names with authority files

############################################################

def load_pickled(filename):
    with open(filename, "rb") as fp:   # Unpickling
        return pickle.load(fp)

def retrieve_viaf_search_results(search_index, search_term, auth_source):
    search_url_template = 'http://viaf.org/viaf/search/viaf?query=local.'+search_index+'+all+"'+search_term+'"+and+local.sources+any+"'+auth_source+'"&sortKeys=holdingscount&httpAccept=application/xml'
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
    try:
        # get the page for that address if it exists
        response = requests.get(lc_address).headers
        # use the preferred name (part of the headers)
        lc_name = response['X-PrefLabel']
    except:
        lc_name = None
        pass
    return lc_name

def write_csv(data, output):
    fieldnames = ['name', 'lcname']
    with open(output, 'w', newline='',encoding='utf-8-sig') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        dict_writer.writeheader()
        dict_writer.writerows(data)

def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)
    return wrapped

############################################################

# load agents
# filename = input("Enter the path to the data file containing the downloaded agent records (e.g. ./data/people.txt or ./data/corp.txt): ")
filename = './data/corp.txt'

agents = load_pickled(filename)

# agent_type = input('Enter the type of agent records (people or corporate): ')
# if agent_type == 'corporate':
#     search_index = 'corporateNames'
# elif agent_type == 'people':
#     search_index = 'personalNames'
search_index = 'corporateNames'

# source_limit = input('enter the exact name of the name-source to focus on (e.g. local): ')
source_limit = 'Crocodile Cafe'

agents = [i for i in agents if i['names'][0]['source'] == source_limit]
print(len(agents))

spinner = Spinner('searching name authority files...')
state = 'loading'

out_list = []
# while state != 'FINISHED':
for agent in agents[:10]:
    search_term = agent['display_name']['sort_name']
    response = retrieve_viaf_search_results(search_index, search_term, 'lc')
    lc_auth_number = get_lc_auth_from_viaf_data(response)
    if lc_auth_number != '':
        print(lc_auth_number)
        wrapped = wrapper(get_lc_term_name, lc_auth_number)
        print(timeit.timeit(wrapped, number=1))
#         lc_name = get_lc_term_name(lc_auth_number)
#         if lc_name != None:
#             out_list.append({'name': search_term, 'lcname': lc_name})
#             spinner.next()
#     state = 'FINISHED'

# print('found '+str(len(out_list))+' possible lcnaf names')

# write(out_list, './data/lcnaf.csv')

