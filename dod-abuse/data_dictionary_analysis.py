import pandas as pd
from numpy import nan

df = pd.read_csv("/Users/brentbrewington/Downloads/24-F-0024_FY16-FY23_Final.xlsx - FOIA24-F-0024.csv")

int_col_abbrs = ["F5", "F13A", "F13F", "F13G", "F13H", "F26", "F34"]
int_col_names = list()
for abbr in int_col_abbrs:
    for col in df.columns:
        if col.find(abbr) > -1:
            int_col_names.append(col)

for int_col_name in int_col_names:
    df.loc[df[int_col_name] == " ", int_col_name] = nan
    df[int_col_name] = df[int_col_name].astype('Int64')

def series_to_unique_set(pd_series):
    if len(pd_series.unique()) == 1:
        return_val = list(pd_series.unique())[0]
    else:
        return_val = sorted(list({x for x in ''.join({x for x in pd_series})}))
    return return_val

unique_report = str()

for col in df:
    col_series = df[col]
    cardinality = len(col_series.unique())
    unique_report += col + "\n" + "-" * len(col) + "\n" + "Cardinality: " + str(cardinality) + "\n"
    if col in int_col_names:
        min_val, max_val = col_series.min(), col_series.max()
        unique_report += f"Range: {min_val} - {max_val}"
    elif cardinality == 1:
        unique_report += f"Single value: {col_series[0]}\n"
    elif cardinality <= 15:
        unique_values = ["'" + x + "'" for x in col_series.sort_values().unique().tolist()]
        unique_report += "Unique values: " + ', '.join(unique_values) + "\n"
        unique_elements = ["'" + x + "'" for x in series_to_unique_set(col_series)]
        unique_report += "Unique elements: " + ', '.join(unique_elements) + "\n"
    else:
        top_5 = col_series.sort_values(ascending=False).unique()[:5].tolist()
        bottom_5 = col_series.sort_values().unique()[:5].tolist()
        unique_report += 'Top 5 unique values: ' + ", ".join(["'" + str(x) + "'" for x in top_5]) + "\n\n"
        unique_report += 'Bottom 5 unique values: ' + ", ".join(["'" + str(x) + "'" for x in bottom_5]) + "\n\n"
    unique_report += "\n"

print(unique_report)

with open("report.txt", "w") as f:
    f.write(unique_report)

