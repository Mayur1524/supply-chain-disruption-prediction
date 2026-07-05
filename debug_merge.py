import pandas as pd
from country_codes import UN_TO_ISO

ct = pd.read_csv('data/comtrade_clean.csv')
lpi = pd.read_csv('data/lpi_clean.csv')
gdelt = pd.read_csv('data/gdelt_clean.csv')

gdelt_agg = gdelt.groupby('actor1_country').agg(
    event_count=('event_id','count'),
    avg_tone=('avg_tone','mean'),
    avg_goldstein=('goldstein','mean')
).reset_index()
gdelt_agg.columns = ['code','event_count','avg_tone','avg_goldstein']

ct['reporter_code'] = ct['reporter_code'].astype(str)
ct['iso_code'] = ct['reporter_code'].map(UN_TO_ISO)

lpi['code'] = lpi['code'].astype(str)
features = ct.merge(lpi, left_on='iso_code', right_on='code', how='left')
features = features.merge(gdelt_agg, left_on='iso_code', right_on='code', how='left', suffixes=('', '_gdelt'))

print('LPI matched:', features['lpi_score'].notna().sum(), '/', len(features))
print('GDELT matched:', features['event_count'].notna().sum(), '/', len(features))
print(features[['reporter_code','iso_code','lpi_score','event_count','avg_goldstein']].head(10))