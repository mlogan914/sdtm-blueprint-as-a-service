import pandas as pd

# Load matched metadata
match_df = pd.read_csv("match_results.csv")

# Filter to a single domain to scaffold
sample_domain = "DM"
domain_df = (
    match_df[match_df["SDTM_Domain"] == sample_domain]
    .dropna(subset=["SDTM_Variable"])
    .sort_values(by="Ordinal", na_position="last")
)

sql_lines = ["SELECT"]

for i, row in domain_df.iterrows():
    sdtm_var = row["SDTM_Variable"]
    src_var = row["ODM_Variable"].lower()
    mapping_type = row["Mapping_Type"]
    sdtm_label = row["SDTM_Label"] or ""
    derived_target = row.get("Derived_Target", "").lower()

    # Determine line content based on mapping type
    if mapping_type == "Direct":
        line = f"    {src_var} AS {sdtm_var}  -- {sdtm_label}"

    elif mapping_type == "Derived":
        inputs = src_var
        if derived_target and derived_target != sdtm_var.lower():
            sdtm_var = derived_target.upper()  # Fix target if alias says so
        line = f"    -- TODO: Derivation required for {sdtm_var}"
        line += f"\n    {{% raw %}}{{{{ derive_{sdtm_var.lower()}({inputs}) }}}}{{% endraw %}} AS {sdtm_var}"

    elif mapping_type == "SUPPQUAL":
        # Skip in main SELECT, handled separately
        continue

    else:
        line = f"    -- TODO: Unmatched or unknown mapping for {src_var} → {sdtm_var}"

    # Add comma unless it's the last row
    sql_lines.append(line + ",")

# Remove trailing comma from last column
if sql_lines[-1].endswith(","):
    sql_lines[-1] = sql_lines[-1][:-1]

# Add FROM clause
sql_lines.append(f"FROM {{% raw %}}{{{{ ref('raw_{sample_domain.lower()}') }}}}{{% endraw %}};")

# Output SQL
sql_output = "\n".join(sql_lines)
print(sql_output)
