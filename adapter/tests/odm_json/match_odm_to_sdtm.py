import json
import csv
from pathlib import Path
from typing import Dict, List

def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)

def flatten_sdtm_metadata(sdtm_json: Dict) -> Dict:
    lookup = {}
    for domain, domain_data in sdtm_json.items():
        for var, meta in domain_data.get("variables", {}).items():
            lookup[(domain, var)] = {
                "SDTM_Domain": domain,
                "SDTM_Variable": var,
                "SDTM_Label": meta.get("label", ""),
                "Ordinal": meta.get("ordinal", "")
            }
    return lookup

def match_odm_to_sdtm(odm_json: Dict, sdtm_lookup: Dict) -> List[Dict]:
    item_defs = odm_json["MetaDataVersion"]["ItemDefs"]
    results = []

    for item in item_defs:
        oid = item["OID"]
        name = item["Name"]
        label = item.get("Label", "")
        aliases = item.get("Aliases", [])

        parts = oid.split(".")
        inferred_domain = parts[1] if len(parts) > 2 else None
        inferred_var = parts[2] if len(parts) > 2 else name

        match_key = (inferred_domain, inferred_var)
        match = sdtm_lookup.get(match_key)
        match_type = "OID" if match else None
        mapping_type = "Direct" if not aliases else "Unmatched"
        alias_context = ""
        alias_name = ""
        alias_label = ""

        # Pre-fill with fallback label
        qlabel_alias = next((a for a in aliases if "QLABEL" in a.get("Context", "")), None)
        fallback_label = qlabel_alias["Name"] if qlabel_alias else item.get("Label", "")

        for alias in aliases:
            context = alias.get("Context", "")
            name_in_alias = alias.get("Name", "")

            if context.startswith("SUPPQUAL") and name_in_alias:
                alias_context = context
                alias_name = name_in_alias
                alias_label = fallback_label
                mapping_type = "SUPPQUAL"
                match_type = "Alias.SUPP"
                match = {
                    "SDTM_Domain": f"SUPP{inferred_domain}",
                    "SDTM_Variable": "QVAL",
                    "SDTM_Label": "Qualifier Value",
                    "Ordinal": ""
                }
                break

            elif context == "DERIVATION_RULE" and name_in_alias:
                alias_context = context
                alias_name = name_in_alias
                mapping_type = "Derived"
                match_type = "Alias.Derivation"
                domain, var = inferred_domain, name_in_alias
                match = sdtm_lookup.get((domain, var))
                break

        if not match:
            mapping_type = "Unmatched"

        results.append({
            "ItemOID": oid,
            "ODM_Variable": name,
            "ODM_Domain": inferred_domain or "",
            "Alias_Context": alias_context,
            "Alias_Name": alias_name,
            "Alias_Label": alias_label,
            "Mapping_Type": mapping_type,
            "Match_Type": match_type if match else "Unmatched",
            "SDTM_Domain": match.get("SDTM_Domain", "") if match else "",
            "SDTM_Variable": match.get("SDTM_Variable", "") if match else "",
            "SDTM_Label": match.get("SDTM_Label", "") if match else "",
            "Ordinal": match.get("Ordinal", "") if match else "",
            "QNAM": alias_name if mapping_type == "SUPPQUAL" else "",
            "QLABEL": alias_label if mapping_type == "SUPPQUAL" else "",
            "IDVAR": inferred_domain if mapping_type == "SUPPQUAL" else "",
            "IDVARVAL": name if mapping_type == "SUPPQUAL" else ""
        })

    return results

def save_to_csv(data: List[Dict], output_path: str):
    with open(output_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def main(odm_path: str, sdtm_path: str, output_csv: str):
    odm_json = load_json(odm_path)
    sdtm_json = load_json(sdtm_path)
    sdtm_lookup = flatten_sdtm_metadata(sdtm_json)
    matched = match_odm_to_sdtm(odm_json, sdtm_lookup)
    save_to_csv(matched, output_csv)
    print(f"✅ Match results written to: {output_csv}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--odm", required=True, help="Path to ODM-collected metadata JSON")
    parser.add_argument("--sdtm", required=True, help="Path to SDTM IG metadata JSON")
    parser.add_argument("--output", required=True, help="Output CSV path for match results")
    args = parser.parse_args()
    main(args.odm, args.sdtm, args.output)
