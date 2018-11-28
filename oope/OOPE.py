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

sql = """
SELECT
  hq_name,
  COUNT(DISTINCT organisation_code) AS branches,
  SUM(item_count) AS items,
  SUM(item_pay_oope_amt)/SUM(item_count) AS oope_per_item,
  MAX(item_pay_oope_amt/item_count) AS max_oope_per_item
FROM
  `ebmdatalab.dispensers.dispensing_with_metadata`
WHERE year_month = '201703'
GROUP BY
  hq_name
ORDER BY
  oope_per_item DESC
"""
df = pd.io.gbq.read_gbq(sql, 'ebmdatalab', dialect='standard')

df.head(10)

# %matplotlib inline
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
df.hist(ax=ax, column=['oope_per_item'], bins=50)
ax.set_yscale('log')

print("The median OOPE is %s" % df.oope_per_item.median())

print ("The worst 10 HQs account for %s items" % df['items'].head(10).sum())
print("About the same (%s) as the best 7" % df['items'].tail(7).sum())

# ## How does high OOPE covary with group size?
#
# None of the large multiples has high mean OOPEs:

df.plot.scatter(x='branches', y='oope_per_item')

# # Investigate worst and best 10ish

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
for name in list(df.hq_name.head(10)):
    hq_names.append("hq_name = '%s'" % name)
baddies = pd.io.gbq.read_gbq(sql % " OR ".join(hq_names), 'ebmdatalab', dialect='standard')

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
for name in list(df.hq_name.tail(7)):
    hq_names.append("hq_name = '%s'" % name)
goodies = pd.io.gbq.read_gbq(sql % " OR ".join(hq_names), 'ebmdatalab', dialect='standard')

baddies.head(1)

# ### The worst 10 HQs 
# ...are accounted for by 12 dispensers, with a mean item count of 9165, mean NIC of £66,000, and mean OOPE of £5770. 3.5% of prescription items come with OOPEs (compared with 0 for the best dispensers). In a single month they charged £69,000 in OOPE, equivalent to a 9% surcharge.

baddies.groupby("name").sum()

# ### The best 7 HQs 
# ...are also accounted for by 12 dispensers, with a mean item count of 8390, mean NIC of £73,000, and mean OOPE of £0 (indeed, a maximum OOPE of £0)

goodies.head(1)

# + {"scrolled": true}
goodies.groupby("name").sum()
# -

# ## Do the best and worst dispense very different things?
#
# No, they look quite similar, although things that were not dispensed at all in the "good" dispensaries appear to have higher per-item OOPE.
#
# There are 4836 presentations represented, of which 1090 only appear in the "good" dispensers, and 1098 in the "bad", leaving 2648 in both.  Descriptive statistics for the "bad" and "good" groups are very similar.
#
# The mean OOPE per item in the "bad" group was 11p. For presentations not actually dispensed in the "good" group, the mean OOPE per item was 18p; presentations also dispensed in the "good" group had a mean OOPE per item of 8p.
#

df3 = baddies.groupby('bnf_name').sum()
df3['oope_per_item'] = df3['item_pay_oope_amt'] / df3['item_pay_dr_nic']
baddy_presentations = df3.sort_values('oope_per_item', ascending=False)
baddy_presentations.describe()

df3 = goodies.groupby('bnf_name').sum()
df3['oope_per_item'] = df3['item_pay_oope_amt'] / df3['item_pay_dr_nic']
goody_presentations = df3.sort_values('oope_per_item', ascending=False)
goody_presentations.describe()

# Now compare these
#baddy_presentations = df3[(df3['oope_per_item'] > 0) & (df3['item_count'] > 10)]
compared = baddy_presentations.merge(
    goody_presentations,
    left_index=True,
    right_index=True,
    suffixes=["_bad", "_good"],
    how="outer"
)
compared.sort_values("oope_per_item_bad", ascending=False)

import numpy as np
good_only = compared[np.isnan(compared['item_count_bad'])]
bad_only = compared[np.isnan(compared['item_count_good'])]
both = compared[(~np.isnan(compared['item_count_good'])) & (~np.isnan(compared['item_count_bad']))]

good_only.describe()

bad_only.describe()

both.describe()

#
