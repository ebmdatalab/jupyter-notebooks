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
# %matplotlib inline

# # What are items are generating the most OOPE?
#
# * The most expensive single presentation is Cinacalcet HCl_Tab 30mg, costing £16,000 per month in OOPE
#   * Calcium and Magnesium supplements overall cost £25,000 per month in OOPE with a mean OOPE of £3.30
# * The most expensive single OOPE is for Tretinoin Cap 10mg with OOPE cost of £80.99
# * The most expensive commonly-prescribed presentation is Solgar_Mag Cit Tab 200mg with mean OOPE per item of £9.86
# * At a BNF paragraph level, the most expensive things are:
#    * Vitamin D (£67,000 per month)
#    * Foods for Special Diets (£52,000 per month)
#    * Enteral Nutrition (£43,000 per month)

# A [recent case of a pharmacist being suspended](https://www.pharmacyregulation.org/sites/default/files/determinations/tasleem_fatma_2063889_determination.pdf) gives some background to how OOPE overcharging might happen. In this case (2013)it was carelessness and inexperience:
#
#  * It affected Aciferol D3, Amlostin, Glutafin G/F bread, Mepradec capsules, ProD3 4, Simvador tablets
#  * These were branded generics, prescribed as brand by GP on grounds they were cheaper (10%) that DT price
#  * But there were not available from the usual wholesaler
#  * They were therefore put through as "specials" to their alternative wholesaler (Pharmacare)
#  * Each order to Pharmacare incurs a £50 plus VAT handling fee and a £15 plus VAT administration fee
#
# It was confirmed [on Twitter](https://twitter.com/CPPEOli/status/1082224683167244289) that the £36.98 amount mentioned below is the standard "special obtains" fee charged by Alliance; which they will always charge for items they don't usually hold.
#
#

# +
sql = """
SELECT
  SUM(item_count) AS items,
  SUM(item_pay_oope_amt) AS oope,
  bnf_code,
  bnf_name
FROM
  `ebmdatalab.dispensers.dispensing_with_metadata`
WHERE year_month = '201703' AND item_pay_oope_amt > 0
GROUP BY bnf_code, bnf_name
ORDER BY SUM(item_pay_oope_amt) DESC
LIMIT 1000
"""

items = pd.io.gbq.read_gbq(sql, 'ebmdatalab', dialect='standard')
# -

items['oope_per_item'] = items['oope'] / items['items']
items.head(3)

items[items['items'] > 100].sort_values('oope_per_item', ascending=False).head(3)

# Grouped at BNF paragraph level
items['bnf_para'] = items['bnf_code'].str.slice(0,6)
items.groupby('bnf_para').agg(['mean', 'sum']).sort_values(('oope', 'sum'), ascending=False).head(10)

# # How does it change over time?
#
# In the period for which we have data, OOPE has decreased overall.  This is because the number of items having OOPE added is decreasing; however, the amount of OOPE being added per item is increasing. See charts below.

sql = """SELECT 
  PARSE_DATE("%Y%m_%d", CONCAT(year_month, "_01")) AS date,
  SUM(item_pay_oope_amt) AS oope,
  SUM(CASE WHEN item_pay_oope_amt > 0 THEN item_count ELSE 0 END) AS oope_items,
  SUM(item_count) AS items
FROM
  `ebmdatalab.dispensers.dispensing_with_metadata`
GROUP BY
  year_month
ORDER BY
  year_month
"""
dftime = pd.io.gbq.read_gbq(sql, 'ebmdatalab', dialect='standard')

dftime['oope_per_item'] = dftime['oope'] / dftime['oope_items']
dftime.set_index('date')[['oope']].plot()
dftime.set_index('date')[['oope_per_item']].plot()
dftime.set_index('date')[['oope_items']].plot()


# +
# Look up by CCG
# Add a column in bigquery that matches postcode to CCG


sql = """SELECT 
  PARSE_DATE("%Y%m_%d", CONCAT(year_month, "_01")) AS date,
  SUM(item_pay_oope_amt) AS oope,
  SUM(CASE WHEN item_pay_oope_amt > 0 THEN item_count ELSE 0 END) AS oope_items,
  SUM(item_count) AS items
FROM
  `ebmdatalab.dispensers.dispensing_with_metadata`
  WHERE ccg = '08H'
GROUP BY
  year_month
ORDER BY
  year_month
"""
dftime = pd.io.gbq.read_gbq(sql, 'ebmdatalab', dialect='standard')
# -

dftime['oope_per_item'] = dftime['oope'] / dftime['oope_items']
dftime.set_index('date')[['oope']].plot()
dftime.set_index('date')[['oope_per_item']].plot()
dftime.set_index('date')[['oope_items']].plot()

# ## Is there interesting variation for multiples?

# summarise OOPE spending per item, grouped by HQ
sql = """
SELECT
  hq_name,
  COUNT(DISTINCT organisation_code) AS branches,
  SUM(item_count) AS items,
  SUM(actual_cost) AS actual_cost,
  SUM(CASE WHEN item_pay_oope_amt > 0 THEN item_count ELSE 0 END) AS oope_items,
  SUM(item_pay_oope_amt) AS oope,
  MAX(item_pay_oope_amt/item_count) AS max_oope_per_item
FROM
  `ebmdatalab.dispensers.dispensing_with_metadata`
WHERE year_month = '201703'
GROUP BY
  hq_name
"""
df = pd.io.gbq.read_gbq(sql, 'ebmdatalab', dialect='standard')

print("In a single month, there were {} branches, represented by {} HQs, prescribing {} items".format(
    df['branches'].sum(),
    df['branches'].count(),
    df['items'].sum()))
print("{} items had OOPE added".format(df['oope_items'].sum()))
print("Total OOPE per month £%s ({})" % (round(df['oope']).sum()))

# ## HQs with highest OOPE per item
#
# If we only count HQs with at least 100 OOPE items per month, per branch, then the top-spending (per OOPE item) HQ charges an average of £57 per OOPE item, and 6% of its items have OOPE added.  It charges £10,869 of OOPE in one month.
#
# Of the top 10 HQs, only one was a multiple (i.e. associated with more than contractor/location).
#

df['oope_per_item'] = df['oope'] / df['items']
df['oope_per_oope_item'] = df['oope'] / df['oope_items']
df['percent_oope_items'] = round(df['oope_items'] / df['items'] * 100)
df['percent_oope_cost'] = round(df['oope'] / df['actual_cost'] * 100)
df = df.sort_values('oope_per_oope_item', ascending=False)
common_oopers = df[df['oope_items']/df['branches'] > 100]

common_oopers.head(13)

common_oopers.sort_values('percent_oope_cost', ascending=False).head(5)

# ## Distribution of OOPE per item by HQ
# The  majority of HQs have no OOPE at all. All but six have their mean OOPE across all items of under 50p; 87% had a mean OOPE of less than 1p.  In the first chart, note the log scale!

print("{}% of contracts never charge any OOPE".format(round(df[df['oope'] == 0].count().iloc[0] / df.count().iloc[0] * 100)))


bins = pd.cut(df.oope_per_oope_item, 209)
df.groupby(bins)['oope_per_oope_item'].agg(['count']).head()

# %matplotlib inline
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
df.hist(ax=ax, column=['oope_per_item'], bins=50)
ax.set_yscale('log')
ax.set_ylabel('HQ count (log scale)')
ax.set_xlabel('Mean OOPE per item (£)')

# %matplotlib inline
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
df.hist(ax=ax, column=['oope_per_oope_item'], bins=50)
ax.set_ylabel('HQ count')
ax.set_xlabel('Mean OOPE per item that has OOPE (£)')

# ## How does high OOPE covary with group size?
#
# None of the large multiples has high mean OOPEs:

df.plot.scatter(x='branches', y='oope_per_oope_item')

# # Is there anything different about the prescriptions being dispensed?
#
# That is, do the HQs with the highest mean OOPE prescribe different amounts of kinds of things from those with the lowest?

print("The 10 HQs with highest mean OOPE account for %s items" % df['items'].head(10).sum())
print("The 10 HQs with lowest mean OOPE account for %s items" % df['items'].tail(10).sum())

# ## Investigate lowest and highest HQs

sql = """
SELECT
  item_pay_dr_nic,
  item_count,
  item_pay_oope_amt,
  bnf_code,
  bnf_name,
  name,
  postcode
FROM
  `ebmdatalab.dispensers.dispensing_with_metadata`
WHERE year_month = '201703' AND 
(%s)
"""
hq_names = []
for name in list(common_oopers.hq_name.head(10)):
    hq_names.append("hq_name = '%s'" % name)
highest = pd.io.gbq.read_gbq(sql % " OR ".join(hq_names), 'ebmdatalab', dialect='standard')

sql = """
SELECT
  item_pay_dr_nic,
  item_count,
  item_pay_oope_amt,
  bnf_code,
  bnf_name,
  name,
  postcode
FROM
  `ebmdatalab.dispensers.dispensing_with_metadata`
WHERE year_month = '201703' AND 
(%s)
"""
hq_names = []
for name in list(df.hq_name.tail(10)):
    hq_names.append("hq_name = '%s'" % name)
lowest = pd.io.gbq.read_gbq(sql % " OR ".join(hq_names), 'ebmdatalab', dialect='standard')

# ### The 10 HQs with highest OOPE per items
# ...are accounted for by 12 dispensers, with a mean item count of 10300, mean NIC of £73,000, and mean OOPE of £5550. 3.5% of prescription items come with OOPEs (compared with 0 for the best dispensers). In a single month they charged £69,000 in OOPE, equivalent to a 9% surcharge (the highest being 22%). 67% of dispensers have NO OOPE.

totals = highest.groupby("name").sum().sort_values('item_pay_oope_amt', ascending=False)
totals['uplift'] = totals['item_pay_oope_amt']/totals['item_pay_dr_nic']
totals

totals.mean()

# ### The 10  HQs with lowest OOPE per item 
# ...are accounted for by 10 dispensers, with a mean item count of 7739, mean NIC of £58,000, and mean OOPE of £0 (indeed, a maximum OOPE of £0)

lowest.head(1)

lowest.groupby("name").sum()

lowest.groupby("name").sum().mean()

# ## Do the highest and lowest dispense very different things?
#
# Descriptive statistics for the "highest" and "lowest" groups are very similar.
#
# The mean OOPE per item (where OOPE was added at all) in the "highest" group was £36 (and 0 in the "lowest"). The "highest" group had about 120 presentations-with-OOPE not seen in the "lowest" group; for those presentations, the mean OOPE per item was £41; OOPE presentations also dispensed in the "lowest" group had a mean OOPE per item of £26.
#
# Therefore it looks like the "highest" group do routinely add more OOPE for everything; but a lot more for things only they see.
#
#
#

import numpy as np
highest['oope_count'] = np.where(highest['item_pay_oope_amt'] > 0, highest['item_count'], 0)
df3 = highest.groupby('bnf_name').sum()
df3['oope_per_oope_item'] = df3['item_pay_oope_amt'] / df3['oope_count']
highest_presentations = df3.sort_values('oope_per_oope_item', ascending=False)
highest_presentations[~np.isnan(highest_presentations['oope_per_oope_item'])].head()

# The following shows that in the HQs with the highest OOPE per items, 3746 different presentations were dispensed, of which 286 had OOPE, with a mean OOPE per item of £36

highest_presentations.describe()

# And the next table shows in the HQs with the lowest OOPE per items, 3368 items were dispensed with no OOPE

df3 = lowest.groupby('bnf_name').sum()
lowest['oope_count'] = np.where(lowest['item_pay_oope_amt'] > 0, lowest['item_count'], 0)
df3 = lowest.groupby('bnf_name').sum()
df3['oope_per_oope_item'] = df3['item_pay_oope_amt'] / df3['oope_count']
lowest_presentations = df3.sort_values('oope_per_oope_item', ascending=False)
lowest_presentations.describe()

# We can combine the two tables together, to find presentations common to both high and low OOPE dispensers.

# + {"scrolled": false}
# Now compare these
#baddy_presentations = df3[(df3['oope_per_item'] > 0) & (df3['item_count'] > 10)]
compared = highest_presentations.merge(
    lowest_presentations,
    left_index=True,
    right_index=True,
    suffixes=["_high", "_low"],
    how="outer"
)
compared.sort_values("oope_per_oope_item_high", ascending=False).head()
# -

import numpy as np
good_only = compared[np.isnan(compared['item_count_high'])]
bad_only = compared[np.isnan(compared['item_count_low'])]
both = compared[(~np.isnan(compared['item_count_low'])) & (~np.isnan(compared['item_count_high']))]

# There are 758 presentations only prescribed in the dispensaries with the lowest OOPE:

good_only.describe()

# ...and 117 presentations-that-have-OOPE which only prescribed in those with the highest OOPE

bad_only[bad_only['item_pay_oope_amt_high'] > 0].describe()

# ...and 2498 in both, of which 192 have any OOPE:

both[both['item_pay_oope_amt_high'] > 0].describe()

# Total OOPE spent per item, for things prescribed in both places - top 5 (of 192 with any OOPE)
both['oope_per_oope_item_high'].sort_values(ascending=False).head()

# + {"scrolled": true}
# Total OOPE spent per item, for things prescribed in only high-oope places - top 5 (of 103 with any OOPE)
bad_only['oope_per_oope_item_high'].sort_values(ascending=False).head()
# -

# # Finally, there is a weird £36.98 thing going on
# I've noticed a lot of the things with high OOPE have identical OOPE-per item - for example, £20.99, £36.98, and £79, all examined here.
#
# These appear to be fixed OOPE prices, regardless of the item - for example, the relatively common `Bio-Vitamin D3_Cap 800u` costs 44p per pack, but £36.98 fixed OOPE.
#
# At the other end, an unusual special like `Levocarnitine_Oral Soln Paed 1.5g/5ml` costs £1571 per pack, and still £36.98 fixed OOPE.
#
#

sql = """
SELECT
  *
FROM
  dispensers.dispensing_with_metadata
WHERE
  (item_pay_oope_amt / item_count = 36.98
    OR (item_pay_oope_amt / item_count) = 20.99 
    OR (item_pay_oope_amt / item_count) = 79.0)
  AND year_month = '201703'
"""
df = pd.io.gbq.read_gbq(sql, 'ebmdatalab', dialect='standard')


df['oope_per_nic'] = (df['item_pay_oope_amt'] / df['item_count']) / df['item_pay_dr_nic']

print("A total of {} spent in OOPE for items with OOPE at these three levels".format(df['item_pay_oope_amt'].sum()))

df[['bnf_name', 'bnf_code', 'item_pay_dr_nic', 'item_pay_oope_amt', 'oope_per_nic']].sort_values('oope_per_nic', ascending=False).head()

# The most common of these:

# + {"scrolled": true}
df.groupby('bnf_name').agg('sum')['item_count'].sort_values(ascending=False).head(10)
# -

# ## What DT categories are the OOPE items in?
# Only Category C items can be claimed, but:

sql = """
SELECT
  vmpp,
  tariff_category,
  d.name,
  d.hq_name,
  d.bnf_code,
  item_count,
  item_pay_oope_amt,
  actual_cost
FROM
  dispensers.dispensing_with_metadata d
LEFT JOIN
  `dmd.dt_viewer` v
ON
  d.bnf_code = v.bnf_code
WHERE
  year_month = '201703'
  AND v.date = '2017-03-01'
  AND item_pay_oope_amt > 0
  AND tariff_category != "Part VIIIA Category C"
"""
df = pd.io.gbq.read_gbq(sql, 'ebmdatalab', dialect='standard')
df.head()

print("A total of {} OOPE was paid on things that shouldn't".format(df.item_pay_oope_amt.sum()))

df.groupby('tariff_category').count()

#
