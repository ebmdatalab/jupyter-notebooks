import glob
import re
import pandas as pd
import string
import dateparser

dates = []
df = pd.DataFrame()
for name in glob.glob("*xls*"):
    d = re.match(r".*hare (?:- )?(.*)\.x", name).groups()[0]
    if d[-1] not in string.digits:
        d = d[:-1]  # remove the version letter
    d = d.replace(" 20", " ").replace(" v2", "")
    d = d[:-2] + "20" + d[-2:]
    dt = dateparser.parse(d, locales=['en-GB'], settings={'PREFER_DAY_OF_MONTH': 'first'})
    this_df = pd.read_excel(name)
    this_df['Date'] = dt

    df = df.append(this_df[['Date', 'ODS', 'Principal Supplier', 'Principal System']])
df.to_csv("complete.csv")

# feb 2018 is missing
