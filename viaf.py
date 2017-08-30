#!/usr/bin/env python

import pickle
from lxml import etree
import requests
from progress.spinner import Spinner
import timeit
import csv

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
    # get the page headers for that address if it exists
    response = requests.get(lc_address).headers
    # use the preferred name (part of the headers)
    lc_name = response['X-PrefLabel']
    return lc_name

# def write_csv(data, output):
#     fieldnames = ['name', 'lcname']
#     with open(output, 'w', newline='',encoding='utf-8-sig') as output_file:
#         dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
#         dict_writer.writeheader()
#         dict_writer.writerows(data)

# def write_txt(name, lcname, output):
#     with open(output, 'w') as file:
#         file.write(name)
#         file.write('\t')
#         file.write(lcname)
#         file.write('\n')

# http://pythoncentral.io/time-a-python-function/
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

source_limit = input('enter the exact name of the name-source to focus on (e.g. local): ')

agents = [i for i in agents if i['names'][0]['source'] == source_limit]
print(len(agents))

spinner = Spinner('searching name authority files...')
state = 'loading'

# out_list = []
out_file = open('./data/lcnaf.csv', 'w')
writer = csv.writer(out_file, delimiter='\t')
while state != 'FINISHED':
    for agent in agents[:10]:
        search_term = agent['display_name']['sort_name']
        response = retrieve_viaf_search_results(search_index, search_term, 'lc')
        lc_auth_number = get_lc_auth_from_viaf_data(response)
        if lc_auth_number != '':
            # print(lc_auth_number)
            # wrapped = wrapper(get_lc_term_name, lc_auth_number)
            # print(timeit.timeit(wrapped, number=1))
            lc_name = get_lc_term_name(lc_auth_number)
            if lc_name != None:
                # out_list.append((search_term, lc_name))
                writer.writerow((search_term, lc_name))
                # out_file.write(search_term)
                # out_file.write('\t')
                # out_file.write(lc_name)
                # out_file.write('\n')
                spinner.next()
            else:
                spinner.next()
        else:
            spinner.next()
    state = 'FINISHED'
out_file.close()

# print('found '+str(len(out_list))+' possible lcnaf names')

# with open('./data/lcnaf.txt', 'w') as fp:
#     fp.write('\n'.join('%s %s' % x for x in out_list))

# for i in out_list:
#     write_txt(i[0], i[1], './data/lcnaf.txt')

# write(out_list, './data/lcnaf.csv')

