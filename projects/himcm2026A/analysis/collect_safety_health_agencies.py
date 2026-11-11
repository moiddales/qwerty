from collect_safety_health import *
cs=list(csv.DictReader((BASE/'data/metadata/cities.csv').open()))
a=[('S08','https://cde.ucr.cjis.gov/LATEST/agency/byStateAbbr/'+st,'fbi_agencies_'+st+'.json','agency','live agency registry') for st in sorted({c['state_abbr'] for c in cs})]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(fetch,a))
