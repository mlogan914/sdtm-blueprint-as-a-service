import pandas as pd
from collections import defaultdict
from pathlib import Path

match_df = pd.read_csv("match_results.csv")

# Separate primary and supplemental domains
dm_df = match_df[match_df["SDTM_Domain"] == "DM"]
supp_df = match_df[match_df["Mapping_Type"] == "SUPPQUAL"]

# Function to sort by ordinal
def safe_ordinal(val):
    try:
        return int(val)
    except:
        return float("inf")

# Create dm.sql
def create_dm_sql(df: pd.DataFrame, path: Path):
    grouped = df.groupby("SDTM_Variable")
    lines = ["SELECT"]

    sdtm_vars = sorted(df["SDTM_Variable"].dropna().unique(), key=lambda var: safe_ordinal(df[df["SDTM_Variable"] == var]["Ordinal"].iloc[0]))

    for i, var in enumerate(sdtm_vars):
        rows = df[df["SDTM_Variable"] == var]
        if len(rows) == 1:
            source = rows.iloc[0]["ODM_Variable"].lower()
            comment = rows.iloc[0]["SDTM_Label"]
            lines.append(f"    {source} AS {var}  -- {comment}")
        else:
            source_vars = ", ".join(rows["ODM_Variable"].str.lower().unique())
            lines.append(f"    -- TODO: Custom transformation for {var}")
            lines.append(f"    -- Source variables: {source_vars}")
            lines.append(f"    {{% raw %}}{{{{ derive_{var.lower()}({source_vars}) }}}}{{% endraw %}} AS {var}")

        if i < len(sdtm_vars) - 1:
            lines[-1] += ","

    lines.append("FROM {% raw %}{{ ref('raw_dm') }}{% endraw %};")

    path.write_text("\n".join(lines))
    print(f"✅ Wrote {path.name}")

# Create suppdm.sql
def create_suppdm_sql(df: pd.DataFrame, path: Path):
    grouped = df.groupby("QNAM")
    lines = ["SELECT"]

    fields = [
        "STUDYID", "RDOMAIN", "USUBJID", "IDVAR", "IDVARVAL",
        "QNAM", "QLABEL", "QVAL"
    ]
    for i, field in enumerate(fields):
        lines.append(f"    {field.lower()} AS {field}" + ("," if i < len(fields) - 1 else ""))

    lines.append("FROM {% raw %}{{ ref('raw_suppdm') }}{% endraw %};")

    path.write_text("\n".join(lines))
    print(f"✅ Wrote {path.name}")

# Output
create_dm_sql(dm_df[dm_df["Mapping_Type"] != "SUPPQUAL"], Path("dm.sql"))
create_suppdm_sql(supp_df, Path("suppdm.sql"))

## -- End of Program Code -- ##