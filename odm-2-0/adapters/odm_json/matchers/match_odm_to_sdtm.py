import json
import csv
from pathlib import Path
from typing import Dict, List, Tuple

from adapters.odm_json.utils.load_paths import load_paths

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
                "Ordinal": meta.get("ordinal", ""),
                "Core": meta.get("core", ""),
                "Role": meta.get("role", ""),
                "Datatype": meta.get("datatype", ""),
                "Description": meta.get("description", ""),
                "CodeList": meta.get("codelist", ""),
                "SDTM_Path": meta.get("sdtm_path", "")
            }
    return lookup

def parse_odm_items(odm_json: Dict) -> Dict[Tuple[str, str], Dict]:
    item_defs = odm_json["MetaDataVersion"]["ItemDefs"]
    results = {}
    for item in item_defs:
        oid = item["OID"]
        name = item.get("Name", "").upper()
        aliases = item.get("Aliases", [])
        parts = oid.split(".")
        if len(parts) < 3:
            continue
        domain, var = parts[1], parts[2]
        results[(domain, var)] = {
            "ItemOID": oid,
            "ODM_Variable": var,
            "ODM_Domain": domain,
            "Aliases": aliases,
            "Raw_Input_Name": name
        }
    return results

def parse_aliases(aliases: List[Dict]) -> Dict:
    result = {
        "Alias_Context": "",
        "Alias_Name": "",
        "Alias_Label": "",
        "Mapping_Type": "Direct",
        "Match_Type": "OID",
        "Derived_Target": "",
        "QNAM": "",
        "QLABEL": "",
        "IDVAR": "",
        "IDVARVAL": "",
        "Not_Submitted": False
    }
    for alias in aliases:
        context = alias.get("Context", "")
        name = alias.get("Name", "")
        if context == "DERIVATION_RULE":
            result["Mapping_Type"] = "Derived"
            result["Match_Type"] = "Alias.Derivation"
            result["Derived_Target"] = name
        elif context.startswith("SUPPQUAL"):
            result["Mapping_Type"] = "SUPPQUAL"
            result["Match_Type"] = "Alias.SUPP"
            if "QNAM" in context:
                result["QNAM"] = name
            elif "QLABEL" in context:
                result["QLABEL"] = name
                result["Alias_Label"] = name
            elif "IDVAR" in context:
                result["IDVAR"] = name
            elif "IDVARVAL" in context:
                result["IDVARVAL"] = name
            result["Alias_Context"] = context
            result["Alias_Name"] = name
        elif context == "NOT_SUBMITTED":
            result["Mapping_Type"] = "Not_Submitted"
            result["Match_Type"] = "Alias.NotSubmitted"
            result["Alias_Context"] = context
            result["Alias_Name"] = name
            result["Not_Submitted"] = True
    return result

def match_odm_to_sdtm_all(odm_json: Dict, sdtm_lookup: Dict) -> List[Dict]:
    odm_vars = parse_odm_items(odm_json)
    odm_domains = set(domain for (domain, _) in odm_vars.keys())

    filtered_sdtm_lookup = {k: v for k, v in sdtm_lookup.items() if k[0] in odm_domains}
    all_keys = set(filtered_sdtm_lookup.keys())

    results = []

	# Pass 1: matched or unmatched SDTMIG vars
    for key in all_keys:
        domain, var = key
        match = filtered_sdtm_lookup.get(key, {})
        odm_info = odm_vars.get(key)

        alias_info = {}
        if odm_info:
            alias_info = parse_aliases(odm_info.get("Aliases", []))

        results.append({
            "ItemOID": odm_info["ItemOID"] if odm_info else "",
            "ODM_Variable": odm_info["ODM_Variable"] if odm_info else "",
            "ODM_Domain": odm_info["ODM_Domain"] if odm_info else domain,
            "Raw_Input_Name": odm_info.get("Raw_Input_Name", "") if odm_info else "",
            "Alias_Context": alias_info.get("Alias_Context", ""),
            "Alias_Name": alias_info.get("Alias_Name", ""),
            "Alias_Label": alias_info.get("Alias_Label", ""),
            "Mapping_Type": alias_info.get("Mapping_Type", "Unmatched") if not odm_info else alias_info.get("Mapping_Type", "Direct"),
            "Match_Type": alias_info.get("Match_Type", "Missing") if not odm_info else alias_info.get("Match_Type", "OID"),
            "Derived_Target": alias_info.get("Derived_Target", ""),
            "SDTM_Domain": match.get("SDTM_Domain", domain),
            "SDTM_Variable": match.get("SDTM_Variable", var),
            "SDTM_Label": match.get("SDTM_Label", ""),
            "Ordinal": match.get("Ordinal", ""),
            "Core": match.get("Core", ""),
            "Role": match.get("Role", ""),
            "Datatype": match.get("Datatype", ""),
            "Description": match.get("Description", ""),
            "CodeList": match.get("CodeList", ""),
            "SDTM_Path": match.get("SDTM_Path", ""),
            "QNAM": alias_info.get("QNAM", ""),
            "QLABEL": alias_info.get("QLABEL", ""),
            "IDVAR": alias_info.get("IDVAR", ""),
            "IDVARVAL": alias_info.get("IDVARVAL", ""),
            "Not_Submitted": alias_info.get("Not_Submitted", False)
        })

    # Pass 2: include unmatched ODM variables that map to SUPP
    for key, odm_info in odm_vars.items():
        if key in all_keys:
            continue # already processed above
        alias_info = parse_aliases(odm_info.get("Aliases", []))
        if alias_info.get("Mapping_Type") == "SUPPQUAL":
            results.append({
                "ItemOID": odm_info["ItemOID"],
                "ODM_Variable": odm_info["ODM_Variable"],
                "ODM_Domain": odm_info["ODM_Domain"],
                "Raw_Input_Name": odm_info.get("Raw_Input_Name", ""),
                "Alias_Context": alias_info.get("Alias_Context", ""),
                "Alias_Name": alias_info.get("Alias_Name", ""),
                "Alias_Label": alias_info.get("Alias_Label", ""),
                "Mapping_Type": "SUPPQUAL",
                "Match_Type": "Alias.SUPP",
                "Derived_Target": "",
                "SDTM_Domain": f"SUPP{odm_info['ODM_Domain']}",
                "SDTM_Variable": "QVAL",
                "SDTM_Label": "Qualifier Value",
                "Ordinal": "",
                "Core": "",
                "Role": "",
                "Datatype": "",
                "Description": "",
                "CodeList": "",
                "SDTM_Path": "",
                "QNAM": alias_info.get("QNAM", ""),
                "QLABEL": alias_info.get("QLABEL", ""),
                "IDVAR": alias_info.get("IDVAR", ""),
                "IDVARVAL": alias_info.get("IDVARVAL", ""),
                "Not_Submitted": alias_info.get("Not_Submitted", False)
            })

    return results

def save_to_csv(data: List[Dict], output_path: str):
    with open(output_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def main(study: str, env: str):
    paths = load_paths(study, env)

    odm_path = paths["crf_metadata_json"]
    sdtm_path = paths["sdtmig_normalized_json"]
    output_csv = paths["match_output_csv"]

    odm_json = load_json(odm_path)
    sdtm_json = load_json(sdtm_path)
    sdtm_lookup = flatten_sdtm_metadata(sdtm_json)

    matched = match_odm_to_sdtm_all(odm_json, sdtm_lookup)
    save_to_csv(matched, output_csv)

    print(f"✅ Match results written to: {output_csv}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", required=True, help="Study name (e.g., VEXIN-03)")
    parser.add_argument("--env", default="dev", help="Environment profile")
    args = parser.parse_args()
    main(args.study, args.env)


## -- End Program Code -- ##