import pandas as pd
import yaml
import argparse
import logging
from pathlib import Path

"""
scaffold_sql.py (patched)
- Inlines custom & standard derivation snippets instead of using `{% include %}` so dbt can compile models.
- Inlines prep_input_cte.sql content too.
- Only uses `.sql` files for derivations (not .txt)
- Removes redundant `AS <var>` suffix when derivation files already contain it
- Adds raw_<domain>. prefix when raw column name matches the SDTM variable name to avoid ambiguity
"""

# Resolve paths relative to script location
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent

config_dir = project_root / "config"
overrides_dir = project_root / "overrides"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def load_yaml(path: Path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_csv(path: Path):
    return pd.read_csv(path)

def read_sql_file(path: Path):
    """Read a .sql file if it exists, return (content, path). Otherwise return (None, path)."""
    if path.exists() and path.suffix == ".sql":
        with open(path, "r") as f:
            return f.read().strip(), path
    return None, path

def inject_variable_line(
    var: str,
    domain: str,
    mapping_type: str,
    standard_deriv_vars: set,
    custom_deriv_vars: set,
    custom_path: Path,
    standard_path: Path,
):
    var_upper = var.upper()
    var_lower = var.lower()
    comment = ""

    if mapping_type == "Direct":
        # Always use raw_<domain>.<var> to avoid name masking
        return f"    ,raw_{domain.lower()}.{var_lower} AS {var_upper}"

    # Standard derivation
    if var_upper in standard_deriv_vars:
        deriv_file = standard_path / f"derive_{var_lower}.sql"
        deriv_code, used_path = read_sql_file(deriv_file)
        if deriv_code:
            logging.info(f"[{domain}] Injecting standard derivation for: {var_upper} from {used_path}")
            return f"    -- Injected standard: {used_path.name}\n    ,{deriv_code}"
        else:
            logging.warning(f"[{domain}] Standard derivation listed but file missing: derive_{var_lower}.sql")
            comment = f"  -- TODO: Standard derivation file missing for {var_upper}"

    # Custom derivation
    if var_upper in custom_deriv_vars:
        deriv_file = custom_path / f"derive_{var_lower}.sql"
        deriv_code, used_path = read_sql_file(deriv_file)
        if deriv_code:
            logging.info(f"[{domain}] Injecting custom derivation for: {var_upper} from {used_path}")
            return f"    -- Injected custom: {used_path.name}\n    ,{deriv_code}"
        else:
            logging.warning(f"[{domain}] Custom derivation listed but file missing: derive_{var_lower}.sql")
            comment = f"  -- TODO: Custom derivation file missing for {var_upper}"

    # Unhandled derived
    if mapping_type == "Derived":
        logging.info(f"[{domain}] Derived variable identified with no derivation listed: {var_upper}")
        comment = f"  -- TODO: Derived variable {var_upper} needs a derivation"

    return f"    ,NULL AS {var_upper}{comment}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV produced by matching ODM to SDTMIG metadata")
    parser.add_argument("--output_dir", required=True, help="Where to write scaffold_<domain>.sql")
    parser.add_argument("--materialized", default="view", help="dbt materialization (default: view)")
    args = parser.parse_args()

    df = load_csv(Path(args.input))
    standard_config = load_yaml(config_dir / "standard_derivations.yml")
    custom_config = load_yaml(config_dir / "custom_derivations.yml")

    standard_deriv_vars = set(standard_config.get("standard_derivations", []))
    domain = df["SDTM_Domain"].dropna().unique()[0].upper()
    custom_deriv_vars = set(custom_config.get("custom_derivations", {}).get(domain, []))

    mapping_vars = set(df["SDTM_Variable"].dropna().str.upper())
    all_known_vars = mapping_vars.union(standard_deriv_vars).union(custom_deriv_vars)

    custom_path = overrides_dir / "custom" / domain.lower()
    standard_path = overrides_dir / "standard"

    lines = []

    # dbt model header
    lines.append("{{ config(materialized='" + args.materialized + "') }}")
    lines.append("")

    # ============================================
    # Step 1: Pre-Merge Input Data (optional CTE)
    # ============================================
    prep_cte_file = custom_path / "prep_input_cte.sql"
    if prep_cte_file.exists():
        with open(prep_cte_file, "r") as f:
            prep_cte_sql = f.read().strip()
        lines.append("-- ============================================")
        lines.append("-- Step 1: Pre-Merge Input Data")
        lines.append("-- ============================================")
        lines.append("-- Injected from: " + str(prep_cte_file))
        lines.append(prep_cte_sql)
        from_clause = f"FROM {domain.lower()}_input"
    else:
        # Reference the (already created) raw_<domain> model directly
        from_clause = f"FROM {{{{ ref('raw_{domain.lower()}') }}}}"


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

    first = True
    for var in ordered_vars:
        mapping_type_series = df[df["SDTM_Variable"].str.upper() == var]["Mapping_Type"].values
        mapping_type = mapping_type_series[0] if len(mapping_type_series) else "unmatched"
        line = inject_variable_line(
            var=var,
            domain=domain,
            mapping_type=mapping_type,
            standard_deriv_vars=standard_deriv_vars,
            custom_deriv_vars=custom_deriv_vars,
            custom_path=custom_path,
            standard_path=standard_path,
        )
        if first:
            line = line.replace("    ,", "    ", 1)
            first = False
        lines.append(line)

    lines.append("")
    lines.append(from_clause)

    output_path = Path(args.output_dir) / f"scaffold_{domain.lower()}.sql"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    logging.info(f"✅ Generated SQL scaffold → {output_path}")

if __name__ == "__main__":
    main()
