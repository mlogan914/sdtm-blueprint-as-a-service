import pandas as pd
from collections import defaultdict
from pathlib import Path

match_df = pd.read_csv("match_results.csv")

# Separate primary and supplemental domains
dm_df = match_df[match_df["SDTM_Domain"] == "DM"]
supp_df = match_df[match_df["Mapping_Type"] == "SUPPQUAL"]

def safe_ordinal(val):
    try:
        return int(val)
    except:
        return float("inf")

# Create dm.sql
def create_dm_sql(df: pd.DataFrame, path: Path):
    grouped = df.groupby("SDTM_Variable")
    lines = ["SELECT"]

    sdtm_vars = sorted(
        df["SDTM_Variable"].dropna().unique(),
        key=lambda var: safe_ordinal(df[df["SDTM_Variable"] == var]["Ordinal"].iloc[0])
    )

    for i, var in enumerate(sdtm_vars):
        group = df[df["SDTM_Variable"] == var]
        row = group.iloc[0]
        mapping_type = row["Mapping_Type"]
        sdtm_label = row["SDTM_Label"]
        sources = ", ".join(group["ODM_Variable"].dropna().str.lower().unique())

        if mapping_type == "Direct":
            lines.append(f"    ,{sources} AS {var}  -- {sdtm_label}")

        elif mapping_type == "Derived":
            lines.append(f"    -- Derived variable: {var}")
            if sources:
                lines.append(f"    -- Candidate inputs: {sources}")
            lines.append(f"    ,{{% raw %}}{{{{ derive_{var.lower()}(...) }}}}{{% endraw %}} AS {var}  -- {sdtm_label}")

        elif mapping_type == "Unmatched":
            lines.append(f"    -- TODO: Unmatched variable: {var}")
            if sources:
                lines.append(f"    -- Candidate sources: {sources}")
            lines.append(f"    ,null AS {var}  -- {sdtm_label}")

    lines.append("FROM {% raw %}{{ ref('raw_dm') }}{% endraw %};")
    path.write_text("\n".join(lines))
    print(f"✅ Wrote {path.name}")

# Create suppdm.sql using UNION logic
def create_suppdm_sql(df: pd.DataFrame, path: Path):
    grouped = df.groupby("QNAM")
    blocks = []

    for qnam, group in grouped:
        row = group.iloc[0]
        qlabel = row["QLABEL"]
        idvar = row["IDVAR"]
        idvarval = row["IDVARVAL"]
        source = row["ODM_Variable"].lower()

        block = [
            "SELECT",
            f"    studyid",
            f"    ,'SUPPDM' AS RDOMAIN",
            f"    ,usubjid",
            f"    ,'{idvar}' AS IDVAR",
            f"    ,{idvarval.lower()} AS IDVARVAL",
            f"    ,'{qnam}' AS QNAM",
            f"    ,'{qlabel}' AS QLABEL",
            f"    ,{source} AS QVAL",
            "FROM {% raw %}{{ ref('raw_dm') }}{% endraw %}",
            f"WHERE {source} IS NOT NULL"
        ]

        blocks.append("\n".join(block))

    sql = "\nUNION ALL\n".join(blocks) + ";"
    path.write_text(sql)
    print(f"✅ Wrote {path.name}")

# Output both
create_dm_sql(dm_df[dm_df["Mapping_Type"] != "SUPPQUAL"], Path("dm.sql"))
create_suppdm_sql(supp_df, Path("suppdm.sql"))
