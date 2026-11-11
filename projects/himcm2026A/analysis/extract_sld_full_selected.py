"""Retain every SLD field for selected block groups, including future-use covariates."""
from collect_foundation import PROJECT
import pandas as pd

out=PROJECT/'data/extracted/mobility_opportunities'
mapping=pd.read_csv(out/'sld_city_bg_spatial_selection.csv',dtype=str)
ids=set(mapping.bg_geoid2019)
parts=[]
for chunk in pd.read_csv(PROJECT/'data/raw/mobility_opportunities/epa_sld_v3_2021.csv',dtype=str,chunksize=20000):
    chunk['bg_geoid2019']=chunk.STATEFP.str.zfill(2)+chunk.COUNTYFP.str.zfill(3)+chunk.TRACTCE.str.zfill(6)+chunk.BLKGRPCE
    parts.append(chunk[chunk.bg_geoid2019.isin(ids)])
result=pd.concat(parts,ignore_index=True)
assert result.bg_geoid2019.is_unique and set(result.bg_geoid2019)==ids
result.to_csv(out/'sld_selected_block_groups_all_source_fields.csv.gz',index=False,compression='gzip')
print('SLD complete selected fields:',len(result),'block groups,',len(result.columns),'columns')
