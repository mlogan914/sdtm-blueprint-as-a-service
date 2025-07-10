import argparse
import pandas as pd
from collections import defaultdict
from pathlib import Path
import yaml
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Load standard derivations from YAML
with open("config/standard_derivations.yml") as f:
    standard_config = yaml.safe_load(f)
STANDARD_DERIVATIONS = set(map(str.upper, standard_config.get("standard_derivations", [])))


def safe_ordinal(val):
    try:
        return int(val)
    except:
        return float("inf")

def create_domain_sql(df: pd.DataFrame, domain: str, path: Path):
    grouped = df.groupby("SDTM_Variable")
    lines = ["SELECT"]

    sdtm_vars = sorted(
        df["SDTM_Variable"].dropna().unique(),
        key=lambda var: safe_ordinal(df[df["SDTM_Variable"] == var]["Ordinal"].iloc[0])
    )

    for var in sdtm_vars:
        group = df[df["SDTM_Variable"] == var]
        row = group.iloc[0]
        target = row["Derived_Target"] if pd.notna(row.get("Derived_Target")) else var
        mapping_type = row["Mapping_Type"]
        sdtm_label = row["SDTM_Label"]
        sources = ", ".join(group["ODM_Variable"].dropna().str.lower().unique())

        if mapping_type == "Direct":
            lines.append(f"    ,{sources} AS {var}  -- {sdtm_label}")
        elif mapping_type == "Derived":
            var_upper = var.upper()
            if var_upper in STANDARD_DERIVATIONS:
                logging.info("[{}] Injecting standard derivation for: {}".format(domain, var_upper))
                lines.append("    ,{{% include 'overrides/standard/derive_{}.sql' %}} AS {}  -- {}".format(
                    var.lower(), target, sdtm_label))
            else:
                logging.info("[{}] Identified custom derivation needed for: {}".format(domain, var_upper))
                lines.append("    -- TODO: Custom derivation for {}".format(target))
                lines.append("    ,null AS {}  -- {}".format(target, sdtm_label))
        elif mapping_type == "Unmatched":
            lines.append(f"    -- TODO: Unmatched variable: {var}")
            if sources:
                lines.append(f"    -- Candidate sources: {sources}")
            lines.append(f"    ,null AS {var}  -- {sdtm_label}")

    lines.append("FROM {% raw %}{{ ref('raw_{{ domain.lower() }}') }}{% endraw %};")
    path.write_text("\n".join(lines))
    print(f"✅ Generated SQL scaffold → {path}")

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
            f"    ,{str(idvarval).strip().lower() if pd.notna(idvarval) else 'null'} AS IDVARVAL",
            f"    ,'{qnam}' AS QNAM",
            f"    ,'{qlabel}' AS QLABEL",
            f"    ,{source} AS QVAL",
            "FROM {% raw %}{{ ref('raw_{{ domain.lower() }}') }}{% endraw %}",
            f"WHERE {source} IS NOT NULL"
        ]

        blocks.append("\n".join(block))

    sql = "\nUNION ALL\n".join(blocks) + ";"
    path.write_text(sql)
    print(f"✅ Generated SQL scaffold → {path}")

def main():
    parser = argparse.ArgumentParser(description="Generate SQL scaffolds from ODM-SDTM matched metadata.")
    parser.add_argument("--input", required=True, help="Path to matched metadata CSV file")
    parser.add_argument("--output_dir", required=True, help="Directory to save scaffolded SQL files")
    args = parser.parse_args()

    match_df = pd.read_csv(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dm_df = match_df[match_df["SDTM_Domain"] == "DM"]
    supp_df = match_df[match_df["Mapping_Type"] == "SUPPQUAL"]

    domains = match_df["SDTM_Domain"].dropna().unique()
    for domain in domains:
        domain_df = match_df[(match_df["SDTM_Domain"] == domain) & (match_df["Mapping_Type"] != "SUPPQUAL")]
        if not domain_df.empty:
            create_domain_sql(domain_df, domain, output_dir / f"scaffold_{domain.lower()}.sql.j2")
    create_suppdm_sql(supp_df, output_dir / "scaffold_suppdm.sql.j2")

if __name__ == "__main__":
    main()
