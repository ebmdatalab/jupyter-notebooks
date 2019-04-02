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

from ebmdatalab.bq import cached_read
import matplotlib.pyplot as plt
import pandas as pd

# +
vendors = pd.read_csv('vendors.csv')
# Clean up the input data
vendors['Principal Supplier'] = vendors['Principal Supplier'].str.strip()
vendors.loc[vendors['Principal Supplier'] == 'INPS', 'Principal Supplier'] = 'Vision'  # seems they changed in 2017
vendors = vendors.loc[vendors['Date'] > '2016-02-01']  # there is some dirty data ("Unknowns") before this

start = pd.to_datetime('2016-01-01')
mid = pd.to_datetime('2017-01-01')
end = pd.to_datetime('2018-12-01')

# +
from ebmdatalab import bq
import importlib
importlib.reload(bq)
measures = ['diltiazem']

def get_data(measure_id):
    sql = """
SELECT
  TRIM(Principal_Supplier) AS supplier,
  m.practice_id,
  m.pct_id,
  m.month,
  numerator,
  denominator,
  '{measure_id}' AS measure_id
FROM
  measures.practice_data_{measure_id} m
JOIN
  hscic.vendors software
ON
  software.ODS = practice_id
  AND Date = m.month
JOIN
  hscic.practices
ON
  practices.code = software.ODS
JOIN
  hscic.practice_statistics
ON
  practice_statistics.practice = practices.code
  AND Date = DATE(practice_statistics.month)
WHERE
  practices.setting = 4
  AND total_list_size > 100
  AND practices.status_code = 'A'
  AND denominator > 0
ORDER BY
  month""".format(measure_id=measure_id)
    import pandas as pd
    df = bq.cached_read(sql, csv_path="data/diltiazem.csv.zip".format(measure_id))
    return df


df = get_data('diltiazem')
# -

df['calc_value'] = df['numerator'] / df['denominator']
df['month'] = pd.to_datetime(df['month'])


df.groupby(['month', 'supplier']).mean()['calc_value'].unstack().plot.line()
plt.legend(loc='best')
plt.title("diltiazem measure, mean values per supplier")

df.rename(columns={'pct_id':'pct'}, inplace=True)  # The CCG column must be named 'pct' for the maps function
by_pct = df[df['month'] == end].groupby('pct').sum().reset_index()
by_pct['calc_value'] = by_pct['numerator'] / by_pct['denominator']
by_supplier_and_pct = df.groupby(['supplier', 'pct']).sum().reset_index()
by_supplier_and_pct['calc_value'] = by_supplier_and_pct['numerator'] / by_supplier_and_pct['denominator']

# + {"scrolled": false}
from ebmdatalab import charts
import matplotlib.gridspec as gridspec
from ebmdatalab import maps
import importlib
importlib.reload(maps)

plt.figure(figsize=(12,8))
layout = gridspec.GridSpec(2, 2)
left_ax = plt.subplot(layout[0, 0])
right_subplot = layout[0:2, 1]



charts.deciles_chart(
        df,
        period_column='month',
        column='calc_value',
        title="Diltiazem measure nationally",
        ylabel="proportion",
        show_outer_percentiles=True,
        show_legend=False,
    ax=left_ax
    )
maps.ccg_map(by_pct, title="Diltiazem measure (all suppliers)", 
             column='calc_value', cartogram=True,
             show_legend=False,
             subplot_spec=right_subplot)

plt.show()

# + {"scrolled": false}


plt.figure(figsize=(20,30))
layout = gridspec.GridSpec(8, 4)
for i, supplier in enumerate(['EMIS', 'TPP', 'Microtest', 'Vision']):
    left_ax = plt.subplot(layout[i * 2, 0])
    right_subplot = layout[(i * 2):(i * 2 + 2), 1]
    #print("right subplot layout[%s]" % (2 - i % 2))
    #print("left ax layout[%s:%s, 0]" % ((i * 2), (i * 2 + 2)))
    #continue
    charts.deciles_chart(
        df[df['supplier'] == supplier],
        period_column='month',
        column='calc_value',
        title="Diltiazem measure for {}".format(supplier),
        ylabel="proportion",
        show_outer_percentiles=True,
        show_legend=False,
        ax=left_ax
    )
    left_ax.set_ylim([0, 1])
    maps.ccg_map(
        by_supplier_and_pct[by_supplier_and_pct['supplier'] == supplier], 
        column='calc_value', 
        show_legend=False,
        cartogram=True, 
        subplot_spec=right_subplot)
plt.show()
# -

# ## What do CCGs with a 50/50 emis/tpp split look like?

single_month = df[df['month'] == end]

by_pct_and_supplier = single_month.groupby(['pct', 'supplier']).count().reset_index()
by_pct = single_month.groupby(['pct']).count().reset_index()

# Create a list of CCGs in which between them TPP and EMIS roughly equally dominate the market
both = by_pct_and_supplier.merge(by_pct, how='inner', left_on='pct', right_on='pct')
both['proportion'] = both['practice_id_x'] / both['practice_id_y']
proportions = both[['pct', 'supplier_x', 'proportion']]
interesting_pcts = []
for key, rows in proportions.groupby('pct'):
    emis = tpp = None
    for i, row in rows.iterrows():
        if row['supplier_x'] == 'EMIS':
            emis = row['proportion']
        elif row['supplier_x'] == 'TPP':
            tpp = row['proportion']
    if emis is not None and tpp is not None:
        if emis > 0.4 and tpp > 0.4 and abs(emis - tpp) > 0.06:
            interesting_pcts.append(key)

qwe = pd.DataFrame(interesting_pcts)
qwe['interesting'] = 100
qwe.columns = ['pct', 'interesting']

plt.figure(figsize=(6,4))
qwe = pd.concat([qwe, pd.DataFrame([{'pct': '99P', 'interesting': 0}])])
maps.ccg_map(
        qwe, 
        column='interesting', 
        show_legend=False,
        title='Locations of 50/50 CCGs',
        cartogram=True)
plt.show()

# + {"scrolled": false}
# Plot them side-by-side
for ccg in interesting_pcts:
    plt.figure(figsize=(12,8))
    layout = gridspec.GridSpec(2, 2)
    for cell, supplier in enumerate(['TPP', 'EMIS']):
        data = df[(df['supplier'] == supplier) & (df['pct'] == ccg)]
        charts.deciles_chart(
            data,
            period_column='month',
            column='calc_value',
            title="Diltiazem measure for {} ({}, n={})".format(ccg, supplier, data.practice_id.count()),
            ylabel="proportion",
            show_outer_percentiles=False,
            show_legend=False,
            ax=plt.subplot(layout[cell])
        )
    plt.show()
# -

# ## Finding practices that swap

two_dates = vendors[(vendors.Date == '2017-01-01') | (vendors.Date == '2018-12-01')]

two_dates.groupby(['ODS', 'Principal Supplier', 'Date'])['Principal Supplier'].count().head(20)

changes = two_dates.groupby(
    ['ODS', 'Principal Supplier', 'Date'])['Principal Supplier'].count().unstack().unstack()
changes.head()

change_dates = pd.DataFrame(vendors.groupby(['ODS', 'Principal Supplier'])['Date'].max()).groupby('ODS')['Date'].min()

import numpy as np
def from_vendor(df, vendor):
    no_longer = df[(df['2017-01-01', vendor] == 1.0) & (df['2018-12-01', vendor] != 1.0)]
    still = no_longer[~(np.isnan(no_longer['2018-12-01', 'EMIS'])&np.isnan(no_longer['2018-12-01', 'TPP'])&np.isnan(no_longer['2018-12-01', 'Vision']))]
    vendors[vendors['ODS'] == ]
    still['switch_date'] = # last date we see vendor for 
    return still
from_tpp = from_vendor(changes, 'TPP')
from_emis = from_vendor(changes, 'EMIS')
from_vision = from_vendor(changes, 'Vision')
from_microtest = from_vendor(changes, 'Microtest')

from_emis.head()

from_emis.count()

from_tpp.count()

# Create two groups of equal size (should really match to population number too)
tpp_to_emis = from_tpp[from_tpp['2018-12-01', 'EMIS'] == 1.0]
emis_to_tpp = from_emis[from_emis['2018-12-01', 'TPP'] == 1.0]

to_emis_data = tpp_to_emis.reset_index().merge(df, how='inner', left_on='ODS', right_on='practice_id')
to_tpp_data = emis_to_tpp.reset_index().merge(df, how='inner', left_on='ODS', right_on='practice_id')

to_tpp_data[to_tpp_data['month'] == start]['calc_value'].describe()

to_tpp_data[to_tpp_data['month'] == end]['calc_value'].describe()

to_emis_data[to_emis_data['month'] == start]['calc_value'].describe()

to_emis_data[to_emis_data['month'] == end]['calc_value'].describe()

# + {"scrolled": false}
print ("Switchers to TPP")
for practice_id in to_tpp_data.practice_id.unique():
    _, ax = plt.subplots()
    charts.deciles_chart(
        to_tpp_data,
        period_column='month',
        column='calc_value',
        title="Diltiazem measure - {}".format(practice_id),
        ylabel="proportion",
        show_outer_percentiles=False,
        ax=ax)
    
    practice_data = to_tpp_data[to_tpp_data['practice_id'] == practice_id]
    plt.plot(practice_data['month'], practice_data['calc_value'], 'r-')
    ax.axvline(pd.to_datetime(change_dates[practice_id]), color='g', linestyle='--', lw=2)


# + {"scrolled": false}
print ("Switchers to EMIS")
for practice_id in to_emis_data.practice_id.unique():
    _, ax = plt.subplots()
    charts.deciles_chart(
        to_emis_data,
        period_column='month',
        column='calc_value',
        title="Diltiazem measure - {}".format(practice_id),
        ylabel="proportion",
        show_outer_percentiles=False,
        ax=ax)
    
    practice_data = to_emis_data[to_emis_data['practice_id'] == practice_id]
    plt.plot(practice_data['month'], practice_data['calc_value'], 'r-')
    ax.axvline(pd.to_datetime(change_dates[practice_id]), color='g', linestyle='--', lw=2)

