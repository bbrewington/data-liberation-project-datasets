import sweetviz as sv
import pandas as pd

# To create the parquet file, follow instructions to open project in DuckDb
# and run this statement:
# COPY (SELECT * FROM int__foia_24_f_0024) TO 'int__foia_24_f_0024.parquet' (FORMAT parquet);

# Then run this:
df = pd.read_parquet("../dod-abuse/dod_abuse/int__foia_24_f_0024.parquet")

# Create sweetviz report & save to HTML
report = sv.analyze(df)
report.show_html("foia_data_report.html")
