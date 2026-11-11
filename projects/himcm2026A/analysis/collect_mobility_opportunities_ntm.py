"""Fetch official NTM agency-level snapshot counts and schema, without rebuilding networks."""
import json,urllib.parse
from collect_mobility_opportunities import fetch,RAW
for kind in ['Stops','Routes']:
 base=f'https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_National_Transit_Map_{kind}/FeatureServer/0/query'
 params={'where':'1=1','groupByFieldsForStatistics':'ntd_id,feed_id','outStatistics':json.dumps([{'statisticType':'count','onStatisticField':'OBJECTID','outStatisticFieldName':'record_count'}]),'returnGeometry':'false','f':'json','resultRecordCount':2000}
 fetch([base+'?'+urllib.parse.urlencode(params),f'bts_ntm_{kind.lower()}_agency_counts.json','S18','2026-09-23 snapshot','NTD agency/feed','US federal government dataset; derived server-side count of records; route records can repeat route IDs across shapes'])
