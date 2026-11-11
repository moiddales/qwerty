"""Verify NYC spatial selection via unpaginated object-ID lists, then fetch attributes by ID."""
import json,urllib.parse
from collect_mobility_opportunities import fetch,RAW
f=next(f for f in json.loads((RAW/'census_acs2025_city_polygons.json').read_text())['features'] if f['attributes']['GEOID']=='3651000');geom=f['geometry'];geom['spatialReference']={'wkid':4326}
base='https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer/1/query'
for relation,name in [('esriSpatialRelContains','contained'),('esriSpatialRelIntersects','intersecting')]:
 p={'geometry':json.dumps(geom),'geometryType':'esriGeometryPolygon','inSR':4326,'spatialRel':relation,'returnIdsOnly':'true','f':'json'}
 n=f'epa_nyc_{name}_objectids.json';fetch([base,n,'S16','2021','NYC BG spatial selection','US federal data',p]);j=json.loads((RAW/n).read_text());ids=j['objectIds'];print(name,len(ids),flush=True)
 for i in range(0,len(ids),1000):
  p={'objectIds':','.join(map(str,ids[i:i+1000])),'outFields':'OBJECTID,GEOID20','returnGeometry':'false','f':'json'}
  fetch([base+'?'+urllib.parse.urlencode(p),f'epa_nyc_{name}_validated_{i}.json','S16','2021','NYC BG spatial selection','US federal data'])
