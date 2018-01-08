
#
# libraries
#
import requests
import pickle
import datetime
import pytz
import codecs
import json
import glob
import os

#
# user settings
#
url = 'https://jobs.thermofisher.com/ListJobs/All/Search/tmo-posting-locations/carlsbad/'
get_content = True
data_directory = 'data'
output_directory = 'output'


#
# get first page
#
if get_content:
    r = requests.get(url, verify=False)

#
# get a list of URLs for all pages
#
pages = r.text.split('disabled pager-prev-arrow')[1].split('Next')[0].split('href="')
pages = [x.split('"')[0] for x in pages]
pages = [x for x in pages if x != '' and x.find('https') == -1]

unique_pages = {}
for p in pages:
    unique_pages[p] = None
unique_pages = sorted(unique_pages.keys())
page_1 = unique_pages[0].split('Page-')[0] + 'Page-1'
unique_pages.append(page_1)
unique_pages = sorted(unique_pages)

#
# download each page and save
#
if get_content:
    for url_section in unique_pages:
        dt_utc = datetime.datetime.now(pytz.UTC)
        dt_pt = dt_utc.astimezone(pytz.timezone('America/Los_Angeles'))
        dt_pt_str = str(dt_pt).replace(' ', '_')
        url = 'https://jobs.thermofisher.com:443' + url_section
        page = url_section.split('/')[-1]
        filename = page + '__' + dt_pt_str + '.txt'
        r = requests.get(url, verify=False)
        f = codecs.open(data_directory + '/' + filename, 'w', encoding='UTF-8')
        f.write(r.text + '\n')
        f.close()


#
# process job ID
#
def parse_line(line):
    if line.find('ShowJob') == -1:
        return None
    else:
        return line.split('>')[1].split('<')[0]
        
#
# load the JSON file we are using to record things
#
with open(data_directory + '/record.json') as f:
    record = json.load(f)

#
# analyze the pages
#
dt_utc = datetime.datetime.now(pytz.UTC)
dt_pt = dt_utc.astimezone(pytz.timezone('America/Los_Angeles'))
dt_pt_str = str(dt_pt).replace(' ', '_')
f_out = open(output_directory + '/new__' + dt_pt_str + '.txt', 'w')

filelist = glob.glob(data_directory + '/Page*.txt')
for filename in filelist:
    timestamp = filename.split('__')[1].split('.txt')[0].replace('_', ' ')
    f = open(filename)
    read_job_id = False
    read_job_title = False
    job_id = None
    title = None
    for line in f:
        line = line.strip()
        if line.find('coldisplayjobid') >= 0:
            read_job_id = True
            continue
        if read_job_id:
            job_id = parse_line(line)
            read_job_id = False
            continue
        if line.find('coloriginaljobtitle') >= 0:
            read_job_title = True
            continue
        if read_job_title:
            title = parse_line(line)

            if not None in [job_id, title]:
                if not record.has_key(job_id):
                    record[job_id] = {
                        'titles' : {},
                        'timestamps' : {},
                        }

                    if len(record[job_id]['timestamps']) == 0:
                        f_out.write(job_id + ':  ' + title + '\n')

                    record[job_id]['titles'][title] = None
                    record[job_id]['timestamps'][timestamp] = None

            read_job_title = False
            job_id = None
            title = None
            continue

f_out.close()

#
# save record
#
with open(data_directory + '/record.json', 'w') as f:
    json.dump(record, f)
            
