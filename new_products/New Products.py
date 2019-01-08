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

# # What can we find out about the introduction of brand new products?
#
# The SQL below is saved as a view in BigQuery. It finds all products that currently have prescribing of over 1000 items per month, that were introduced in the last 5 years, per no more recently than 6 months ago.

import pandas as pd
import os

if not os.path.exists('new_chemicals.csv'):
    sql = """WITH
      chemicals AS (
      SELECT
        month,
        DATE_SUB(
      DATE(
        EXTRACT(YEAR FROM CURRENT_DATE()), 
        EXTRACT(MONTH FROM CURRENT_DATE()), 
        1), 
      INTERVAL 5 YEAR) AS start_month, 
        SUBSTR(bnf_code, 1, 9) AS chemical,
        SUM(items) AS items
      FROM
        `ebmdatalab.hscic.normalised_prescribing_standard` rx
      WHERE
        DATE(month) >= DATE_SUB(
      DATE(
        EXTRACT(YEAR FROM CURRENT_DATE()), 
        EXTRACT(MONTH FROM CURRENT_DATE()), 
        1), 
      INTERVAL 5 YEAR) 
        AND DATE(month) <= DATE_SUB(
      DATE(
        EXTRACT(YEAR FROM CURRENT_DATE()), 
        EXTRACT(MONTH FROM CURRENT_DATE()), 
        1), 
      INTERVAL 6 MONTH) -- give it six months
        AND bnf_code not like '2%' -- exclude devices
      GROUP BY
        month,
        chemical,
        SUBSTR(bnf_code, 1, 9)),
      base_month AS (
      SELECT
        chemical,
        start_month,
        month,
        items,
        RANK() OVER (PARTITION BY chemical ORDER BY month) + 1 AS rank
      FROM
        chemicals),
      base_month_offset AS (
      SELECT
        chemical,
        month,
        start_month,
        items,
        RANK() OVER (PARTITION BY chemical ORDER BY month) AS rank
      FROM
        chemicals),
      new_chemicals AS (
      SELECT
        base_month_offset.*
      FROM
        base_month_offset
      LEFT JOIN
        base_month
      ON
        base_month.rank = base_month_offset.rank
        AND base_month.chemical = base_month_offset.chemical
      WHERE
        base_month.chemical IS NULL
      ORDER BY
        base_month_offset.month )
    SELECT
      new_chemicals.chemical AS code,
      bnf.chemical AS chemical,
      new_chemicals.month AS month_introduced,
      new_chemicals.items AS items_in_first_month,
      SUM(latest_month.items) AS items_in_current_month
    FROM
      new_chemicals
    INNER JOIN
      `ebmdatalab.hscic.normalised_prescribing_standard_latest_month` AS latest_month
    ON
      new_chemicals.chemical = SUBSTR(latest_month.bnf_code, 1, 9)
    INNER JOIN
      `ebmdatalab.hscic.bnf` AS bnf
    ON new_chemicals.chemical = bnf.chemical_code
    WHERE start_month != DATE(new_chemicals.month)
    GROUP BY
      new_chemicals.chemical,
      bnf.chemical,
      new_chemicals.items,
      new_chemicals.month,
      new_chemicals.rank
    HAVING
      SUM(latest_month.items) > 1000
    """
    df = pd.read_gbq(sql, 'ebmdatalab', verbose=False, dialect='standard')
    df.to_csv("new_chemicals.csv")
else:
    df = pd.read_csv('new_chemicals.csv')
    df['month_introduced'] = pd.to_datetime(df['month_introduced'])

# %matplotlib inline
intros = df.groupby('month_introduced').count()['code'].reset_index()

months = pd.DataFrame(pd.date_range(start=intros.month_introduced.iloc[0], end=intros.month_introduced.iloc[-1], freq='MS'))
months.columns = ['month']

df2 = months.merge(intros, how="left", left_on="month", right_on="month_introduced")[["month","code"]].set_index("month").fillna(0)
import matplotlib.dates as mdates
import matplotlib.pylab as plt
ax = df2.plot(x_compat=True)
ax.xaxis.set_major_locator(mdates.YearLocator())
plt.show()

# ## Show prescribing rates of each chemical

if not os.path.exists('new_chemicals_prescribing.csv'):
    sql = """
    SELECT
      month,
      chemical,
      SUBSTR(bnf_code, 1, 9) AS chemical_code,
      SUM(items) AS items
    FROM
      `ebmdatalab.hscic.normalised_prescribing_standard` rx
    INNER JOIN
      `ebmdatalab.hscic.bnf` AS bnf
    ON SUBSTR(rx.bnf_code, 1, 9) = bnf.chemical_code
    WHERE
      ({})
    GROUP BY
      month,
      chemical,
      chemical_code
    ORDER BY
      month, chemical
    """
    where = []
    for chemical in df.code:
        where.append("bnf_code LIKE '{}%'".format(chemical))
    where = " OR ".join(where)
    df2 = pd.read_gbq(sql.format(where), 'ebmdatalab', verbose=False, dialect='standard').set_index('month')
    df2.to_csv("new_chemicals_prescribing.csv")
else:
    df2 = pd.read_csv("new_chemicals_prescribing.csv")
    df2['month'] = pd.to_datetime(df2['month'])

df3 = df2.reset_index().set_index(['chemical','month']).unstack('chemical')['items']
df3.plot(kind='area',stacked=True,legend=False)

# ## Just count new drugs 6 months after introduction

# +
from pandas.tseries.offsets import *

sql_template = """SELECT
      month,
      chemical,
      SUBSTR(bnf_code, 1, 9) AS chemical_code,
      SUM(items) AS items
    FROM
      `ebmdatalab.hscic.normalised_prescribing_standard` rx
    INNER JOIN
      `ebmdatalab.hscic.bnf` AS bnf
    ON SUBSTR(rx.bnf_code, 1, 9) = bnf.chemical_code
    WHERE
      bnf_code LIKE '{}%' AND month >= "{}" AND month <= "{}"
    GROUP BY
      month,
      chemical,
      chemical_code"""
sql = []
for index, row in df.iterrows():
    start_date = row['month_introduced']
    code = row['code']
    sql.append(sql_template.format(code, start_date, start_date + DateOffset(months=6) ))
df3 = pd.read_gbq(" UNION ALL ".join(sql), 'ebmdatalab', verbose=False, dialect='standard')
# -

df4 = df3.reset_index().set_index(['chemical','month']).unstack('chemical')['items']
df4.plot(kind='area',stacked=False,legend=False)


# +
# make everything a ratio of what it was at 12 months
# we just want to do a count of new drugs in any given month pre practice.
# If we assume maximum adoption at month N (e.g. 12)
# then we want a measure of a "quick adopter", which could be "adopts a drug within 6 months"
# which is like a moving average?
# Or just 

df5 = pd.DataFrame(index=df4.index)
for column in df4.columns:
    df5[column] = df4[column] / df4[column].max()
df5.plot(kind='area',stacked=True,legend=False)

# +
from pandas.tseries.offsets import *

sql_template = """SELECT
      rx.month,
      rx.practice,
      pct,
      count(items) AS novel_items,
      total_list_size
    FROM
      `ebmdatalab.hscic.normalised_prescribing_standard` rx
    INNER JOIN
      `ebmdatalab.hscic.practice_statistics` stats
    ON stats.practice = rx.practice AND stats.month = rx.month
    WHERE
      {}
    GROUP BY
      rx.month,
      rx.practice, pct, total_list_size"""
where = []
where_template = "(bnf_code LIKE '{}%' AND rx.month = '{}')"
for index, row in df.iterrows():
    start_date = row['month_introduced']
    code = row['code']
    where.append(where_template.format(code, start_date + DateOffset(months=6)))
where = " OR ".join(where)
df6 = pd.read_gbq(sql_template.format(where), 'ebmdatalab', verbose=False, dialect='standard')
# -

#df6.groupby('pct').unstack('pct')
#df3 = df2.reset_index().set_index(['chemical','month']).unstack('chemical')['items']
#df3.plot(kind='area',stacked=True,legend=False)
df6 = df6[df6['total_list_size']> 0]
df6['x'] = (df6['novel_items']  / df6['total_list_size']) 
df6.sort_values('x', ascending=False)
df6.groupby('pct').sum().reset_index().sort_values('x', ascending=False)
# divide this by number of patients or something - bigger practices more likely to prescribe stuff


# + {"scrolled": false}
for chemical_code in df.code:
    title = df2[df2['chemical_code'] == chemical_code]['chemical'].iloc[0]
    df2[df2['chemical_code'] == chemical_code].plot(title=title)
