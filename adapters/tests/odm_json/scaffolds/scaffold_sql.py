import pandas as pd
import yaml
import argparse
import logging
from pathlib import Path

# Resolve paths relative to script location
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent

config_dir = project_root / "config"
overrides_dir = project_root / "overrides"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_csv(path):
    return pd.read_csv(path)

def inject_variable_line(var, domain, mapping_type, standard_deriv_vars, custom_deriv_vars, custom_path, standard_path):
    var_upper = var.upper()
    var_lower = var.lower()
    comment = ""

    if mapping_type == "Direct":
        return f"    ,{var_lower} AS {var_upper}"
    
    elif var_upper in standard_deriv_vars:
        deriv_file = standard_path / f"derive_{var_lower}.sql"
        if deriv_file.exists():
            logging.info(f"[{domain}] Injecting standard derivation for: {var_upper}")
            return f"    ,{{% include 'overrides/standard/derive_{var_lower}.sql' %}} AS {var_upper}"
        else:
            logging.warning(f"[{domain}] Standard derivation listed but file missing: derive_{var_lower}.sql")
            comment = f"  -- TODO: Standard derivation file missing for {var_upper}"
    
    elif var_upper in custom_deriv_vars:
        deriv_file = custom_path / domain.lower() / f"derive_{var_lower}.sql"
        if deriv_file.exists():
            logging.info(f"[{domain}] Injecting custom derivation for: {var_upper}")
            return f"    ,{{% include 'overrides/custom/{domain.lower()}/derive_{var_lower}.sql' %}} AS {var_upper}"
        else:
            logging.warning(f"[{domain}] Custom derivation listed but file missing: derive_{var_lower}.sql")
            comment = f"  -- TODO: Custom derivation file missing for {var_upper}"
    
    elif mapping_type == "Derived":
        logging.info(f"[{domain}] Derived variable identified with no derivation listed: {var_upper}")
        comment = f"  -- TODO: Derived variable {var_upper} needs a derivation"

    return f"    ,NULL AS {var_upper}{comment}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()

    df = load_csv(args.input)
    standard_config = load_yaml("config/standard_derivations.yml")
    custom_config = load_yaml("config/custom_derivations.yml")

    standard_deriv_vars = set(standard_config.get("standard_derivations", []))
    domain = df["SDTM_Domain"].dropna().unique()[0].upper()
    custom_deriv_vars = set(custom_config.get("custom_derivations", {}).get(domain, []))

    mapping_vars = set(df["SDTM_Variable"].dropna().str.upper())
    all_known_vars = mapping_vars.union(standard_deriv_vars).union(custom_deriv_vars)

    custom_path = Path("overrides/custom") / domain.lower()
    standard_path = Path("overrides/standard")

    lines = []

    # ============================================
    # Step 1: Pre-Merge Input Data
    # ============================================
    # This CTE (if present) prepares raw inputs from one or more source datasets
    # into a unified input structure for downstream derivations.
    # The logic is defined in: overrides/custom/<domain>/prep_input_cte.sql
    prep_cte_path = custom_path / "prep_input_cte.sql"
    if prep_cte_path.exists():
        lines.append("-- ============================================")
        lines.append("-- Step 1: Pre-Merge Input Data")
        lines.append("-- ============================================")
        lines.append("-- This CTE (if present) prepares raw inputs from one or more source datasets")
        lines.append("-- into a unified input structure for downstream derivations.")
        lines.append("-- The logic is defined in: overrides/custom/<domain>/prep_input_cte.sql")
        lines.append("{% include 'overrides/custom/" + domain.lower() + "/prep_input_cte.sql' %}")
        from_clause = f"FROM {{ {{ domain.lower() }} }}_input"
    else:
        from_clause = r"FROM {{ ref('raw_' ~ domain.lower()) }}"


    lines.append("")
    # ============================================
    # Step 2: Build SDTM Domain Variables
    # ============================================
    lines.append("-- ============================================")
    lines.append("-- Step 2: Build SDTM Domain Variables")
    lines.append("-- ============================================")
    lines.append("-- This SELECT block builds the SDTM-compliant domain using:")
    lines.append("--  - Direct mappings from source columns")
    lines.append("--  - Standard derivation snippets (injected)")
    lines.append("--  - Custom derivation snippets (injected per domain)")
    lines.append("--  - Null placeholders for unmapped variables (with TODO comments)")
    lines.append("-- Column order is based on SDTMIG metadata")
    lines.append("SELECT")

    ordered_df = df.sort_values("Ordinal", na_position="last") if "Ordinal" in df.columns else df
    ordered_vars = ordered_df["SDTM_Variable"].dropna().str.upper().tolist()

    for var in sorted(all_known_vars):
        if var not in ordered_vars:
            ordered_vars.append(var)

    for var in ordered_vars:
        var_lower = var.lower()
        mapping_type = df[df["SDTM_Variable"].str.upper() == var]["Mapping_Type"].values
        mapping_type = mapping_type[0] if len(mapping_type) else "unmatched"
        line = inject_variable_line(var, domain, mapping_type, standard_deriv_vars, custom_deriv_vars, custom_path, standard_path)
        lines.append(line)

    lines.append("")
    lines.append(from_clause + ";")

    output_path = Path(args.output_dir) / f"scaffold_{domain.lower()}.sql.j2"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    logging.info(f"✅ Generated SQL scaffold → {output_path}")


if __name__ == "__main__":
    main()
