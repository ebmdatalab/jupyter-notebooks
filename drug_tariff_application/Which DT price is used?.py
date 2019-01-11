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

# # Which month's DT is applied to a given month's dispensing?
#
# We've always assumed that the November DT would be the basis for all reimbursment in the month of November, but now we're not so sure.
#
# The following SQL computes the median "price per pill" of all tablets and capsules in November 2018.
#
# It then compares it with the drug tariff (or price concession) price of each of those pills.
#
# We show that Category M presentations use the DT price for the month of dispensing, but Category A presentations use the Drug Tariff of the following month.

import pandas as pd

sql = """WITH
  median_price_per_unit AS (
  WITH
    prices_per_unit AS (
    SELECT
      month AS date,
      bnf_code,
      bnf_name,
      IEEE_DIVIDE(net_cost,quantity) AS price_per_unit
    FROM
      ebmdatalab.hscic.normalised_prescribing_standard)
  SELECT
    DISTINCT date,
    bnf_code,
    bnf_name,
    percentile_cont(price_per_unit,
      0.5) OVER (PARTITION BY date, bnf_code) AS median_price_per_unit
  FROM
    prices_per_unit),
  oct_rx AS (
  SELECT
    date,
    bnf_code,
    bnf_name,
    ROUND(median_price_per_unit, 4) AS median_price_per_unit
  FROM
    hscic.vw__median_price_per_unit AS rx
  WHERE
    (rx.bnf_name LIKE '%_Tab%'
      OR rx.bnf_name LIKE '%_Cap%')
    AND rx.date='2018-10-01'
    AND rx.bnf_code NOT LIKE '0410020C0%AC'),
  sept_dt AS (
  SELECT
    dt.bnf_code,
    tariff_category,
    ROUND(COALESCE(dt.concession,
        dt.price_pence)/dt.quantity/100,4) AS dt_price_per_unit
  FROM
    dmd.dt_viewer AS dt
  WHERE
    dt.date='2018-09-01'),
  oct_dt AS (
  SELECT
    dt.bnf_code,
    tariff_category,
    ROUND(COALESCE(dt.concession,
        dt.price_pence)/dt.quantity/100,4) AS dt_price_per_unit
  FROM
    dmd.dt_viewer AS dt
  WHERE
    dt.date='2018-10-01'),
  nov_dt AS (
  SELECT
    dt.bnf_code,
    tariff_category,
    ROUND(COALESCE(dt.concession,
        dt.price_pence)/dt.quantity/100,4) AS dt_price_per_unit
  FROM
    dmd.dt_viewer AS dt
  WHERE
    dt.date='2018-11-01')
SELECT
  oct_rx.bnf_code,
  oct_rx.bnf_name,
  oct_rx.median_price_per_unit,
  sept_dt.tariff_category AS sept_category,
  sept_dt.dt_price_per_unit AS sept_dt_ppu,
  oct_dt.tariff_category AS oct_category,
  oct_dt.dt_price_per_unit AS oct_dt_ppu,
  nov_dt.tariff_category AS nov_category,
  nov_dt.dt_price_per_unit AS nov_dt_ppu
FROM
  oct_rx
INNER JOIN
  sept_dt
ON
  oct_rx.bnf_code = sept_dt.bnf_code
INNER JOIN
  oct_dt
ON
  oct_rx.bnf_code = oct_dt.bnf_code
INNER JOIN
  nov_dt
ON
  oct_rx.bnf_code = nov_dt.bnf_code"""
df = pd.read_gbq(sql, 'ebmdatalab', dialect='standard', verbose=False)

df = df.set_index('bnf_code')

df.head(1)

# +
# Exclude items which have more than one price (i.e. more than one VMPP in the DT)
# As these complicate our calculations
# -

df2 = df.join(df.groupby('bnf_code').count()['bnf_name'] > 1, rsuffix='x').reset_index()
df2 = df2[df2['bnf_namex'] == False]

df2.groupby('oct_category').count()

# let's disregard anything where the DT never changed
changing = df2[(df2['sept_dt_ppu'] != df2['oct_dt_ppu']) & (df2['nov_dt_ppu'] != df2['oct_dt_ppu'])]
print("There are {} pills which changed price each month during that quarter".format(changing.count()['bnf_code']))

changing[changing['median_price_per_unit'] == changing['sept_dt_ppu']]

asd = df2[(df2['nov_dt_ppu'] != df2['oct_dt_ppu'])].groupby('oct_category').count()

# +
import numpy as np
conditions = [
    (changing['median_price_per_unit'] == changing['sept_dt_ppu']),
    (changing['median_price_per_unit'] == changing['oct_dt_ppu']),
    (changing['median_price_per_unit'] == changing['nov_dt_ppu'])
]

choices = ['sept', 'oct', 'nov']
changing['dt_used'] = np.select(conditions, choices)

# +
import numpy as np
conditions = [
    (asd['median_price_per_unit'] == asd['sept_dt_ppu']),
    (asd['median_price_per_unit'] == asd['oct_dt_ppu']),
    (asd['median_price_per_unit'] == asd['nov_dt_ppu'])
]

choices = ['sept', 'oct', 'nov']
asd['dt_used'] = np.select(conditions, choices)
#df2[(df2['sept_dt_ppu'] != df2['oct_dt_ppu'])
# -

asd.groupby('dt_used').count()

asd[asd['dt_used'] == 'oct'].groupby('oct_category').count()

asd[asd['dt_used'] == 'sept'].groupby('oct_category').count()

# Missing ones - these look like rounding errors to me
changing[changing['dt_used'] == '0']

# +
#Let's take a look at 0501110C0AABHBH Metronidazole_Tab 500mg
# 0501110C0AABHBH	Metronidazole_Tab 500mg	1.8600	Part VIIIA Category A	1.8010	Part VIIIA Category A	1.8281	Part VIIIA Category A	1.8605	False	0
# That could be a rounding error. We have it at 39.06 a pack- 1.8600 per pill
# It was 39.07 in November which is 1.8605
