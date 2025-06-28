import json

def extract_sdtm_metadata(input_json_path):
    """
    Extracts grouped SDTM variable metadata from a CDISC Library JSON export.
    Returns a dictionary structured as:
    {
        "DM": {
            "domain_label": "Demographics",
            "variables": {
                "AGE": {...},
                "SEX": {...},
                ...
            }
        },
        ...
    }
    """
    with open(input_json_path, "r", encoding="utf-8") as f:
        sdtm_data = json.load(f)

    # Build a map of dataset path → domain label
    domain_label_lookup = {
        dataset["_links"]["self"]["href"].split("/")[-1]: dataset["_links"]["self"]["title"]
        for class_obj in sdtm_data.get("classes", [])
        for dataset in class_obj.get("datasets", [])
    }

    grouped = {}
    for class_obj in sdtm_data.get("classes", []):
        for dataset in class_obj.get("datasets", []):
            domain_abbr = dataset["_links"]["self"]["href"].split("/")[-1]
            domain_label = domain_label_lookup.get(domain_abbr, domain_abbr)

            if domain_abbr not in grouped:
                grouped[domain_abbr] = {
                    "domain_label": domain_label,
                    "variables": {}
                }

            for var in dataset.get("datasetVariables", []):
                var_name = var.get("name")
                if not var_name:
                    continue

                grouped[domain_abbr]["variables"][var_name] = {
                    "variable": var_name,
                    "label": var.get("label"),
                    "role": var.get("role"),
                    "datatype": var.get("simpleDatatype"),
                    "core": var.get("core"),
                    "description": var.get("description"),
                    "codelist": var.get("_links", {}).get("codelist", [{}])[0].get("href") if var.get("_links", {}).get("codelist") else None,
                    "sdtm_path": var.get("_links", {}).get("self", {}).get("href")
                }

    return grouped