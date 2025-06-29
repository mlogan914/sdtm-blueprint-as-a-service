import pandas as pd
from collections import defaultdict

# Load your metadata CSV
match_df = pd.read_csv("match_results.csv")

# Pick one SDTM domain to scaffold
sample_domain = "DM"
domain_df = match_df[match_df["SDTM_Domain"] == sample_domain].dropna(subset=["SDTM_Variable"])

# Group by SDTM variable to check for custom transformation needs
grouped = domain_df.groupby("SDTM_Variable")

# Detect variables needing custom transforms:
# - Multiple source ODM_Variables mapped to the same SDTM_Variable
# - Alias used that doesn't match the target SDTM_Variable
custom_transform_vars = {
    var for var, group in grouped if len(group) > 1 or any(
        (row["Alias_Context"] == "SDTM" and row["Alias_Name"] != var)
        for _, row in group.iterrows()
    )
}

# Build the SQL lines
sql_lines = ["SELECT"]
for i, (sdtm_var, group) in enumerate(grouped):
    if sdtm_var in custom_transform_vars:
        # Add macro placeholder for manual or reusable logic
        src_vars = ", ".join(group["ODM_Variable"].str.lower().unique())
        sql_lines.append(f"    -- TODO: Custom transformation required for {sdtm_var}")
        sql_lines.append(f"    -- Source variables: {src_vars}")
        sql_lines.append(f"    {{% raw %}}{{{{ derive_{sdtm_var.lower()}({src_vars}) }}}}{{% endraw %}} AS {sdtm_var}")
    else:
        row = group.iloc[0]
        line = f"    {row['ODM_Variable'].lower()} AS {sdtm_var}  -- {row['SDTM_Label']}"
        sql_lines.append(line)
    if i != len(grouped) - 1:
        sql_lines[-1] += ","

sql_lines.append(f"FROM {{% raw %}}{{{{ ref('raw_{sample_domain.lower()}') }}}}{{% endraw %}};")

# Output final SQL string
sql_output = "\n".join(sql_lines)
print(sql_output)
