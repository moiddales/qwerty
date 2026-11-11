from collect_safety_health import *
items=[
('S14','https://www.samhsa.gov/data/sites/default/files/reports/rpt57010/2025_MH_Facilities_for_All_City_All.xlsx','samhsa_mh_facilities_2025.xlsx','facility','2025'),
('S14','https://www.samhsa.gov/data/sites/default/files/reports/rpt57010/National_Directory_MH_facilities_2025.pdf','samhsa_mh_directory_2025.pdf','documentation','2025'),
('S08','https://cde.ucr.cjis.gov/LATEST/webapp/main.3b78afe6a803d4e1.js','fbi_app.js','documentation','live'),
('S09','https://cdan.dot.gov/tsftables/tsfar.htm','fars_tables.html','documentation','2024 ARF'),
('S12','https://youthonline.cdc.gov/','yrbs_youthonline.html','documentation','live'),
('S12','https://www.cdc.gov/yrbs/supplementary-tables/index.html','yrbs_tables.html','documentation','2023'),
('S12','https://www.cdc.gov/yrbs/data/yrbs-participation.html','yrbs_participation.html','documentation','2025'),
('S15','https://data.cdc.gov/api/views/vgc8-iyc4.json','places_metadata.json','place','2025'),
]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:list(ex.map(fetch,items))
