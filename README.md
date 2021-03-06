# UW MediaSpace

Python scripts to facilitate interaction with the UW Media Archives' local instance of ArchivesSpace via the ArchivesSpace API. Includes scripts to prepare and import data.

## 'Get' Scripts

Use the following scripts:

- **get_agents.py** (get person or corporate entity agent records)

- **get_dos.py** (get digital object records)

- **get_subjects.py** (get subject records)

- **get_resource_aos.py** (get the archival objects of a given resource)

- **get_ethno_aos.py** (get all archival objects in the Ethnomusicology Archives)

- **get_ethno_res.py** (get all resources from the Ethnomusicology Archives)

to extract different types of records stored in ASpace.

## 'POST' Scripts

- Use **aspace_create_new.py** to add a list of new json records to the appropriate location in ASpace.

- Use **aspace_update.py** to update stored records on ASpace with new information (usually generated from one or more other scripts).

## Extracting [LCNAF](http://id.loc.gov/authorities/names.html) names for stored agent records

1. run **get_agents.py** to extract person or corporate name records from ASpace and save that data to a file

2. run **search_viaf_lc.py** to use a modified version of the [Bentley Historical Library's](http://archival-integration.blogspot.com/2015/07/order-from-chaos-reconciling-local-data.html) approach to:

	a. search the [Virtual International Authority File](https://viaf.org/) database for matching name records, 

	b. extract LoC IDs for each match, 

	c. then get the LC term name for each match, 

	d. use fuzzy matching to reconcile potentially mismatched pairs

	e. then search LoC records directly for names lacking a match

	f. and save all that data to a csv for quality control

3. run **add_lcnaf.py.py** on the quality controlled list of names/LCNAF terms to update stored agent records with the LCNAF terms found

4. run **aspace_update.py** to update records on ASpace

## Post-processing ASpace export/Archives West converted EAD documents

- **prepEAD.py**: necessary script to error-correct some issues with the export/conversion process. should be run on the output file generated from the AW-AS converter.

- **croc.py**: extra processing necessary for display purposes for the croc collection (should be run after prepEAD.p)

## Data cleaning scripts (some examples)

- **add_add_AW_terms.py**: add AW browsing terms to ethnomusicology resources based on [HRAF](http://hraf.yale.edu/) and [LCSH](http://id.loc.gov/authorities/subjects.html) subjects already linked to each collection

- **add_findingaid.py**: add template finding aid information to each downloaded resource record

- **clean_agents.py**: clean up agent records imported using the LCNAF plugin on ASpace (remove extra punctuation and extra whitespace, correct name source)

- **digi_to_note.py**: add digitization information from the date field to the note field of archival objects (for display on AW - no date labels)

- **fix_nameorder.py**: if an agent-person name is in direct order, invert it

- **instance_to_do.py**: create digital object records from an archival object's grandchild instance 

	a. then, use **aspace_create_new.py** to POST new digital objects to ASpace

	b. use **get_resource_aos.py** to download the archival object records to update and **get_dos.py** to download the digital objects just created

	c. use **link_ao_do.py** to link those archival objects back to the digital objects just created

	d. use **aspace_update.py** to update archival object records on ASpace

- **prep_text_subjects.py**: prepare a text file containing subject terms (e.g. AW browsing terms) for import into ASpace as formatted json records 

