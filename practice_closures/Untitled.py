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

# +
import pandas as pd
import numpy as np

import logging
logger = logging.getLogger('pandas_gbq')
logger.setLevel(logging.ERROR)

GBQ_PROJECT_ID = '620265099307'

sql = """
SELECT
  month,
  pct_id,
  practice,
  total_list_size
FROM
  `hscic.practice_statistics`
WHERE
  month >= '2015-12-01'
AND 
  month < '2018-10-01'

"""
df = pd.read_gbq(sql, GBQ_PROJECT_ID, dialect='standard')

# -

months = df.month.unique()
months.sort()
months = list(months)

import datetime 
summary = pd.DataFrame()
data = pd.DataFrame()
for m1 in months[:-1]:
    m2 = months[months.index(m1) + 1]
    d1 = df[df.month == m1]
    d2 = df[df.month == m2]
 
    merged = d1.merge(d2, how="left", left_on="practice", right_on="practice")
    merged = merged[['month_x', 'pct_id_x', 'practice', 'total_list_size_x', 'total_list_size_y']]
    merged = merged.rename(columns={'month_x': 'last_open_month', 'pct_id_x': 'pct_id'})
    merged['closed'] = np.isnan(merged['total_list_size_y'])
    conditions = [np.isnan(merged['total_list_size_y']), ~np.isnan(merged['total_list_size_y'])]
    choices = [0 - merged['total_list_size_x'], merged['total_list_size_y'] - merged['total_list_size_x']]
    merged['delta'] = np.select(
        conditions, choices, default=0
    )
    closed = merged[merged['closed'] == True]
    s = pd.DataFrame(
           data={
            'month':m2,
            'closed_count': len(closed),
            'patients_in_closed': closed.total_list_size_x.sum(), 
            'total_change': merged.delta.sum()
           },
    index=[m2])
  
    summary = summary.append(s)
    data = data.append(merged)


data.head(5)

# ## Summary of closure info per month
#
# * An average of 22 practices are closed per month, affecting an average of 82,000 patients
# * An average of 53,000 patients are added to England patient lists per month overall
#
# Note that list sizes were only updated quarterly until April 2017

summary

# # Check against an example we've manually checked

closed_jan_2017 = data[(data.closed==True) & (data.last_open_month == '2016-12-01')]

closed_jan_2017.query("pct_id == '08Q'")

print("The total list size for 08Q changed by {} in Jan 2017".format(
    data[(data.last_open_month == '2016-12-01') & (data.pct_id == '08Q')].delta.sum()))

# ## Can we infer practice list transfers from large closure patient numbers?
#
# Yes, it seems so:

# restrict to when data was monthly
data[(data.last_open_month > '2017-04-01') & (data.closed==True)].sort_values('delta', ascending=True).head()

# So, taking 01K:
data[(data.last_open_month == '2017-06-01') & (data.pct_id=='01K') & (abs(data.delta) > 800)]

# Or 06N
data[(data.last_open_month == '2018-05-01') & (data.pct_id=='06N') & (abs(data.delta) > 800)]

# ## Investigate the very large net changes in Oct 2017
#
# The summary table above shows more than 100k extra patients added in Oct 2017. How come?
#
# Let's find the CCGs with the most change.

data[(data.last_open_month == '2017-09-01')]\
    .groupby('pct_id')\
    .agg({'delta': 'sum', 'closed': 'sum'})\
    .sort_values('delta')\
    .tail()

# So what's going on with 03N?  It had 82 practices both months, with no closures.
#
# The mean list size (7330) increased by 117 patients.  The largest practice had 34,570 patients - an increase of 6855

ccg = data[(data.last_open_month == '2017-09-01') & (data.pct_id == '03N')].sort_values('delta', ascending=False)
ccg.describe()

# The question is where they came from. Only 42 practices had decreasing list sizes, adding up to 628 patients moving elsewhere (or dying):

ccg.head(5)

ccg[ccg.delta < 0].delta.sum()

# We can see that the practice at the top of the list traditionally sheds a few hundred patients a month, but has twice has big increases. It's a University Health Service, so these are new academic years starting.

# So the October change is presumably students enrolling, but the place they're coming from not updating their list sizes.

data[data.practice == 'C88627']

# # Hypothesis
#
# * When a practice closes, its list size usually goes elsewhere in the same CCG
# * If using list size as a denominator, then measure calculations will show zero for those practices
# * If aggregating patient-level numbers up to CCG level, then the prescribing assigned to those practices will disappear
#
# Check:
#
# * Large closures are balanced by large list size increases in same CCG (spot check)
# * That measures in the main site are calculated at CCG level by summing all numerators and denominators (not aggregating up) - yes
# * That the same is true of the RCT analysis - no (see below)
#
# Consequences:
# * Not having merger information means sometimes measures will look different until all the prescribing catches up with the list size data
#
# ## RCT analysis breakdown
#
# Original code [here](https://github.com/ebmdatalab/low-priority-CCG-visit-RCT/blob/853a43626644feb8dc540b2f60407cdb0fb3ab77/outcomes/Primary%20outcome%20measures%20for%20LPP%20RCT.ipynb).
#
# Numerators (cost) and denominators are taken from CCG-level measures computations, so if measures are right, so are those figures.
#
# Items are taken from tables designated `ebmdatalab.alex.items_*`. These are in turn taken from notebooks related to our Low Priority paper, and [archived in figshare](https://figshare.com/articles/The_NHS_England_low-priority_medicines_initiative_has_had_minimal_impact_on_prescribing/6984296). Specifically, the tables are generated by [this SQL](https://gist.github.com/sebbacon/c7a7f7bdc8c6a25494005c8d5dfd9c3d). This computes a ratio for every numerator/denominator pair at a practice level, *then* groups by CCG - significantly, it [excludes anything with a null ratio](https://gist.github.com/sebbacon/c7a7f7bdc8c6a25494005c8d5dfd9c3d#file-measure-sql-L109-L111). Thus we will lose numerators in the final output.

# # Summary 
#
# * September - November each year sees large net list size increases of up to 50,000 more than in other months. This is likely to be university students enrolling and going on their local practice list. These are patients who are either appearing in practice lists for the first time ever, or not also being removed from their previous patient list
# * When a practice closes, its list size usually goes elsewhere in the same CCG, and we can see this happening
# * RCT analysis for CCG visits currently broken; it will under-report `items` numerators where practices have closed but are still seeing significant prescribing. Closures seem to cluster within CCGs as they are often mergers, so this may have affected our analysis

# # Q: How do practice list sizes correlate with total population estimates?
#
# Answer: very well (r=0.99). But interestingly there are consistently about 230,000 more patients on lists than population of England.  This is likely to be a mixture of [ghost patients](http://www.pulsetoday.co.uk/your-practice/practice-topics/practice-income/ghost-patient-drive-comes-back-to-haunt-gps/20007765.article) and a lag due to late reporting after deaths (there are approx 500k per year in the UK).

# +
import pandas as pd
import numpy as np

import logging
logger = logging.getLogger('pandas_gbq')
logger.setLevel(logging.ERROR)

GBQ_PROJECT_ID = '620265099307'


# +
# from https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland

pop = pd.read_csv('MYEB3_summary_components_of_change_series_UK_(2017).csv')
years = range(2001, 2018)
pop = pop[pop.country == 'E'][["population_%s" % y for y in years]]
pop.columns = [str(y) for y in years]
pop = pd.DataFrame(pop.sum())
pop.columns = ["population"]
pop.head(2)
# -


sql = """
SELECT
  month,
  sum(total_list_size) as total_list_size
FROM
  `hscic.practice_statistics_all_years`
WHERE %s
GROUP BY month
"""
conditions = []
for y in years:
    conditions.append("month = '%s-06-01'" % y)
sql = sql % " OR ".join(conditions)
df = pd.read_gbq(sql, GBQ_PROJECT_ID, dialect='standard')

df['year'] = df.month.dt.strftime("%Y")
df = df.set_index("year")
merged = df.join(pop)
merged = merged.sort_values("month")
merged['delta'] = merged['total_list_size'] - merged['population']

merged

merged['population'].corr(merged['total_list_size'])

merged.plot.line(x='month')
