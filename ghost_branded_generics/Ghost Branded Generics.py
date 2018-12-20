# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext_format_version: '1.2'
#   kernelspec:
#     display_name: Python (jupyter virtualenv)
#     language: python
#     name: jupyter
#   language_info:
#     codemirror_mode:
#       name: ipython
#       version: 3
#     file_extension: .py
#     mimetype: text/x-python
#     name: python
#     nbconvert_exporter: python
#     pygments_lexer: ipython3
#     version: 3.6.5
# ---

import pandas as pd

import os
if os.path.exists("ghost_generics.csv.gz"):
    ghost_df = pd.read_csv("ghost_generics.csv.gz", compression='gzip')
else:
    ghost_df = pd.read_gbq("""
SELECT
  prac.ccg_id,
  rx.practice_code,
  rx.bnf_code,
  rx.bnf_description,
  rx.items,
  rx.quantity,
  rx.nic,
  dt.concession,
  dt.quantity AS dt_quantity,
  dt.price_pence,
  SUM(rx.items*rx.quantity) AS QI,
  ROUND(IEEE_DIVIDE(rx.NIC, (rx.items*rx.quantity)),4) AS rx_ppu,
  ROUND(IEEE_DIVIDE((dt.price_pence/100), dt.quantity),4) AS dt_ppu,
  CASE
    WHEN dt.concession IS NOT NULL THEN ROUND(IEEE_DIVIDE((dt.concession/100), dt.quantity), 4)
    ELSE NULL
  END AS concession_ppu
FROM
  richard.prescribing_2018_09_full AS rx
JOIN
  dmd.dt_viewer AS dt
ON
  rx.bnf_code=dt.bnf_code
JOIN
  hscic.practices AS prac
ON
  rx.practice_code=prac.code
WHERE
  (rx.bnf_description LIKE '%_Tab%'
    OR rx.bnf_description LIKE '%_Cap%')
  AND dt.date='2018-09-01'
  AND rx.bnf_code NOT LIKE '0410020C0%AC'
GROUP BY
  prac.ccg_id,
  rx.practice_code,
  rx.bnf_code,
  rx.bnf_description,
  rx.quantity,
  rx.items,
  rx_ppu,
  dt_ppu,
  dt.concession,
  dt.quantity,
  dt.price_pence,
  rx.NIC
HAVING
  rx_ppu <> dt_ppu
""", 'ebmdatalab', dialect='standard', verbose=False)
    ghost_df.to_csv("ghost_generics.csv")


ghost_df.head(1)

ghost_df['dt_or_concession_ppu'] = ghost_df['concession_ppu'].combine_first(ghost_df['dt_ppu'])

total_items = ghost_df['items'].sum()
total_presentations = len(ghost_df['bnf_code'].unique())
cheaper = ghost_df[ghost_df['rx_ppu'].round(3) < ghost_df['dt_or_concession_ppu'].round(3)]['items'].sum()
costlier = ghost_df[ghost_df['rx_ppu'].round(3) > ghost_df['dt_or_concession_ppu'].round(3)]['items'].sum()
same = total_items - (cheaper + costlier)
print("There are {} items prescribed for {} presentations. "
      "{}% are cheaper than DT, {}% more expensive, the rest the same".format(
          total_items,
          total_presentations,
          round(cheaper/total_items * 100),
          round(costlier/total_items * 100)
      ))

ghost_df['excess_ppu'] = ghost_df['rx_ppu'] - ghost_df['dt_or_concession_ppu']
ghost_df['excess_ppu_no_concession'] = ghost_df['rx_ppu'] - ghost_df['dt_ppu']
ghost_df['excess_cost_dt_no_concession'] = (ghost_df['excess_ppu_no_concession']) * ghost_df['QI']
ghost_df['excess_cost_dt'] = (ghost_df['excess_ppu']) * ghost_df['QI']
ghost_df = ghost_df.sort_values('excess_cost_dt', ascending=False)

# # Summary numbers

total_savings = round(ghost_df['excess_cost_dt'].sum())
total_savings_no_concession = round(ghost_df['excess_cost_dt_no_concession'].sum())
print("Total possible savings in Sept 2018: £{}".format(total_savings))


# # Top savings

by_presentation = ghost_df.groupby('bnf_description')[['excess_cost_dt', 'excess_ppu']].sum().reset_index()

# ## 1. By total cost

by_presentation.sort_values('excess_cost_dt',ascending=False).head()

# ## 2. By per-unit price

by_presentation.sort_values('excess_ppu',ascending=False).head()

# # Top costs per CCG

gpd_ghost_df = ghost_df.groupby('ccg_id')['excess_cost_dt'].sum().reset_index().sort_values('excess_cost_dt',ascending=False)

gpd_ghost_df.head(10)

# # Top costs per EPR

epr = pd.read_csv("gpsoc_marketshare_201801b.csv.gz", compression='gzip', usecols=['ODS', 'Principal Supplier', 'Principal System'])
epr.head()

numbers = ghost_df[['practice_code', 'excess_cost_dt']]
by_epr = numbers.merge(epr, how='inner', left_on='practice_code', right_on='ODS')

by_epr.head()

# +
summary = by_epr.groupby('Principal System')['excess_cost_dt', 'practice_code'].agg({'cost': 'sum', 'count': pd.Series.nunique})

summary.columns = ["excess_cost", "rows_count", "practice_count"]
summary['cost_per_install'] = summary['excess_cost'] / summary['practice_count']
#summary = summary.sort_values('cost_per_install', ascending=False)
summary = summary.sort_values('cost_per_install', ascending=False)
# -

summary

# %matplotlib inline
import matplotlib.pyplot as plt 
summary['cost_per_install'].plot.bar()
plt.ylabel("cost per install (£)")

# # Create useful files for CCGs

summary = gpd_ghost_df.assign(saving_from_top_10 = None).set_index('ccg_id')
import re
import os
from zipfile import ZipFile
for ccg_id in summary.index:
    if re.match(r"^[0-9]{2}[A-Z]", ccg_id):
        ccg = ghost_df[ghost_df.ccg_id == ccg_id]
        top_presentations = ccg.groupby('bnf_description').sum().sort_values('excess_cost_dt', ascending=False).head(10).reset_index()[['bnf_description', 'excess_cost_dt']]
        target_prescriptions = top_presentations.merge(ccg, how='left', left_on='bnf_description', right_on='bnf_description').sort_values('excess_cost_dt_y', ascending=False)
        useful_cols = ['practice_code', 'bnf_description', 'bnf_code', 'items', 'excess_cost_dt_y']
        target_prescriptions = target_prescriptions[useful_cols]
        target_prescriptions = target_prescriptions.groupby(['practice_code', 'bnf_description', 'bnf_code']).sum().reset_index()
        target_prescriptions.columns = ['practice_code', 'bnf_description', 'bnf_code', 'items', 'excess_cost']
        summary.loc[ccg_id, 'saving_from_top_10'] = target_prescriptions['excess_cost'].sum()
        f = "{}.csv".format(ccg_id)
        target_prescriptions.to_csv(f)
        with ZipFile("csv_data/{}.zip".format(ccg_id), 'w') as myzip:
            myzip.write(f)
        os.remove(f)
summary = summary.reset_index()

summary.head()
