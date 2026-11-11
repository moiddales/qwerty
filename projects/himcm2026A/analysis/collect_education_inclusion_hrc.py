"""Download city scorecards using the observed official 2025 naming convention.
Candidate URLs are verified by HTTP and PDF magic, not assumed to exist.
Raw HRC PDFs require rights review before redistribution; extracted facts cite each source.
"""
import csv,concurrent.futures
from collect_education_inclusion import BASE,fetch
cities=list(csv.DictReader((BASE/'data/metadata/cities.csv').open()))
def one(c):
 name=c['city_name'].replace(' city (balance)','').replace(' city','')
 if name.startswith('Nashville-Davidson'):name='Nashville'
 if c['state']=='District of Columbia':return
 url='https://hrc-prod-requests.s3-us-west-2.amazonaws.com/files/documents/MEI-Scorecard-Assets/MEI-25-Scorecards/MEI-2025-'+name.replace(' ','-')+'-'+c['state'].replace(' ','-')+'.pdf'
 fetch(url,'hrc_2025_'+c['city_id']+'.pdf','S23','2025','municipality','HRC copyright; local research copy only, do not redistribute raw PDF without permission')
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(one,cities))
