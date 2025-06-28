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
                "SDTM_Label": meta.get("label", "")
            }
    return lookup

def match_odm_to_sdtm(odm_json: Dict, sdtm_lookup: Dict) -> List[Dict]:
    item_defs = odm_json["MetaDataVersion"]["ItemDefs"]
    results = []

    for item in item_defs:
        oid = item["OID"]
        name = item["Name"]
        aliases = item.get("Aliases", [])

        parts = oid.split(".")
        inferred_domain = parts[1] if len(parts) > 2 else None
        inferred_var = parts[2] if len(parts) > 2 else name

        match_key = (inferred_domain, inferred_var)
        match = sdtm_lookup.get(match_key)
        match_type = "OID" if match else None

        # Fallback to alias if OID failed
        if not match:
            for alias in aliases:
                context = alias.get("Context")
                alias_name = alias.get("Name")

                if context == "SDTM":
                    if "." in alias_name:
                        domain, var = alias_name.split(".")
                    else:
                        domain, var = inferred_domain, alias_name
                    match = sdtm_lookup.get((domain, var))
                    if match:
                        match_type = "Alias"
                        break

                elif context == "SDTM.SUPP" and "SUPP" in alias_name:
                    domain = alias_name.replace("SUPP", "").split(".")[0]
                    match = sdtm_lookup.get((f"SUPP{domain}", "QVAL"))
                    if match:
                        match_type = "Alias.SUPP"
                        break

        results.append({
            "ItemOID": oid,
            "ODM_Variable": name,
            "ODM_Domain": inferred_domain or "",
            "Alias_Context": aliases[0]["Context"] if aliases else "",
            "Alias_Name": aliases[0]["Name"] if aliases else "",
            "Match_Type": match_type if match else "Unmatched",
            "SDTM_Domain": match["SDTM_Domain"] if match else "",
            "SDTM_Variable": match["SDTM_Variable"] if match else "",
            "SDTM_Label": match["SDTM_Label"] if match else ""
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
    parser.add_argument("--out", required=True, help="Output CSV path for match results")
    args = parser.parse_args()
    main(args.odm, args.sdtm, args.out)
