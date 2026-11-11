"""Use official city boundaries to select wholly contained SLD block groups.
Outputs boundary-coverage diagnostics; do not label subset means exact city means.
"""
import json,csv,urllib.parse,concurrent.futures
from collect_mobility_opportunities import fetch,RAW,ROOT
cities=list(csv.DictReader((ROOT/'data/metadata/cities.csv').open()))
base='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/18/query'
p={'where':"GEOID IN ("+','.join("'"+c['city_id']+"'" for c in cities)+")",'outFields':'GEOID,NAME,STATE,PLACE','returnGeometry':'true','outSR':4326,'f':'json','geometryPrecision':6}
if not (RAW/'census_acs2025_city_polygons.json').exists():fetch([base+'?'+urllib.parse.urlencode(p),'census_acs2025_city_polygons.json','S03','ACS2025 boundary','25 Census places','US government public domain'])
features=json.loads((RAW/'census_acs2025_city_polygons.json').read_text())['features']
print('city polygon count',len(features),flush=True)
def get(f):
 cid=f['attributes']['GEOID'];geom=f['geometry'];geom['spatialReference']={'wkid':4326}
 for relation,name in [('esriSpatialRelContains','contained'),('esriSpatialRelIntersects','intersecting')]:
  p={'geometry':json.dumps(geom),'geometryType':'esriGeometryPolygon','inSR':4326,'spatialRel':relation,'outFields':'GEOID20','returnGeometry':'false','f':'json','returnIdsOnly':'false','resultRecordCount':5000}
  name0=f'epa_sld_{cid}_{name}.json'
  if not (RAW/name0).exists():fetch(['https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer/1/query',name0,'S16','SLD2021; boundary2025','BG polygon spatial selection','US government public domain',p])
  j=json.loads((RAW/name0).read_text());offset=len(j.get('features',[]))
  while j.get('exceededTransferLimit'):
   p['resultOffset']=offset;page=f'epa_sld_{cid}_{name}_{offset}.json'
   fetch(['https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer/1/query',page,'S16','SLD2021; boundary2025','BG polygon spatial selection','US government public domain',p])
   j=json.loads((RAW/page).read_text());offset+=len(j['features'])
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(get,features))
