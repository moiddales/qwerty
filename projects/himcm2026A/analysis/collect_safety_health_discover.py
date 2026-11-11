from collect_safety_health import *
items=[('S08','https://cde.ucr.cjis.gov/LATEST/webapp/'+n,'fbi_'+n,'documentation','live') for n in ['239.25c516830ef47ef1.js','627.fcd61c633cf91b93.js','842.7109b50e23c658e9.js','896.53d4deb73b029339.js']]
items += [('S12','https://api.us.socrata.com/api/catalog/v1?domains=data.cdc.gov&search_context=data.cdc.gov&q=YRBS&limit=100','yrbs_catalog.json','documentation','live'),('S09','https://cdan.dot.gov/SharedResources/saveSasJobRequest.js','fars_request.js','documentation','live')]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(fetch,items))
