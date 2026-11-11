from collect_safety_health import *
import urllib.parse
def getyear(y):
 for typ in ['offenses-known-to-le','resource-pages']:
  key=f'cius/{y}/{typ}-{y}.zip'
  n=f'fbi_signed_{typ}_{y}.json'
  r=fetch(('S08','https://cde.ucr.cjis.gov/LATEST/s3/signedurl?'+urllib.parse.urlencode({'key':key}),n,'agency',str(y)))
  if r['success']:
   # Refresh the public signed URL in memory; stored discovery JSON is redacted.
   with urllib.request.urlopen('https://cde.ucr.cjis.gov/LATEST/s3/signedurl?'+urllib.parse.urlencode({'key':key}),timeout=90) as response:
    d=json.load(response)
   if key in d:fetch(('S08',d[key],f'fbi_{typ}_{y}.zip','agency',str(y)))
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:list(ex.map(getyear,range(2021,2026)))
