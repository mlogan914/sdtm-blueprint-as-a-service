import argparse
import json
import xml.etree.ElementTree as ET
from lxml import etree
from pathlib import Path

from adapters.odm_json.utils.load_paths import load_paths

NS = {"odm": "http://www.cdisc.org/ns/odm/v2.0"}

# -- Schema Validation
def validate_xml_against_xsd(xml_path: Path, xsd_path: Path):
    """Validate the XML against a given XSD schema, resolving includes."""
    parser = etree.XMLParser(load_dtd=True, no_network=False)

    with open(xsd_path, 'rb') as f:
        schema_doc = etree.parse(f, parser)
        schema = etree.XMLSchema(schema_doc)

    xml_doc = etree.parse(str(xml_path))
    is_valid = schema.validate(xml_doc)

    if not is_valid:
        raise ValueError(f"XML validation failed:\n{schema.error_log}")
    print(f"✅ XML file {xml_path.name} is valid against {xsd_path.name}")

# -- XML Parse
def parse_metadata(xml_path: Path) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    study = root.find("odm:Study", NS)
    if study is None:
        raise ValueError("No <Study> element found – is this valid ODM‑XML?")
    study_oid = study.attrib.get("OID", "UNKNOWN_STUDY")

    mdv = study.find("odm:MetaDataVersion", NS)
    if mdv is None:
        raise ValueError("No <MetaDataVersion> found – export may be incomplete.")

    meta_json = {
        "StudyOID": study_oid,
        "MetaDataVersion": {
            "OID": mdv.attrib.get("OID", "MDV.UNKNOWN"),
            "Name": mdv.attrib.get("Name", ""),
            "ItemDefs": [],
            "CodeLists": [],
            "ItemGroupDefs": [],
        }
    }

    # ----- ItemDefs -----
    for item in mdv.findall("odm:ItemDef", NS):
        fmt = item.attrib.get("DisplayFormat")
        cl_ref = item.find("odm:CodeListRef", NS)
        code_list_oid = cl_ref.attrib.get("CodeListOID") if cl_ref is not None else None
        aliases = []
        is_derived = False
        for alias in item.findall("odm:Alias", NS):
            ctx = alias.attrib.get("Context")
            name_ = alias.attrib.get("Name")
            aliases.append({"Context": ctx, "Name": name_})
            if ctx == "DERIVATION_RULE":
                is_derived = True

        item_entry = {
            "OID": item.attrib.get("OID"),
            "Name": item.attrib.get("Name"),
            "DataType": item.attrib.get("DataType"),
            "Length": item.attrib.get("Length"),
            "Format": fmt,
            "CodeListRef": code_list_oid,
            "Derived": is_derived,
            "Aliases": aliases
        }
        meta_json["MetaDataVersion"]["ItemDefs"].append(item_entry)

    # ----- CodeLists -----
    for cl in mdv.findall("odm:CodeList", NS):
        cl_entry = {
            "OID": cl.attrib.get("OID"),
            "Name": cl.attrib.get("Name"),
            "DataType": cl.attrib.get("DataType"),
            "Items": []
        }
        for cli in cl.findall("odm:CodeListItem", NS):
            coded_val = cli.attrib.get("CodedValue")
            decode_el = cli.find("odm:Decode/odm:TranslatedText", NS)
            decode_text = decode_el.text if decode_el is not None else None
            cl_entry["Items"].append({
                "CodedValue": coded_val,
                "Decode": decode_text
            })
        meta_json["MetaDataVersion"]["CodeLists"].append(cl_entry)

    # ----- ItemGroupDefs -----
    for ig in mdv.findall("odm:ItemGroupDef", NS):
        ig_entry = {
            "OID": ig.attrib.get("OID"),
            "Name": ig.attrib.get("Name"),
            "Type": ig.attrib.get("Type"),
            "Repeating": ig.attrib.get("Repeating"),
            "ItemRefs": []
        }
        for ir in ig.findall("odm:ItemRef", NS):
            ig_entry["ItemRefs"].append({
                "ItemOID": ir.attrib.get("ItemOID"),
                "Mandatory": ir.attrib.get("Mandatory"),
                "RepeatKey": ir.attrib.get("RepeatKey")
            })
        meta_json["MetaDataVersion"]["ItemGroupDefs"].append(ig_entry)

    return meta_json


def main():
    parser = argparse.ArgumentParser(
        description="Extract ODM-XML metadata and write as JSON using config-based paths."
    )
    parser.add_argument("--study", required=True, help="Study folder name")
    parser.add_argument("--env", required=True, help="Environment name in paths.yml (e.g., dev)")
    args = parser.parse_args()

    paths = load_paths(study=args.study, env=args.env)
    xml_path = Path(paths["odm_xml"])
    out_path = Path(paths["crf_metadata_json"])
    xsd_path = paths.get("schemas", {}).get("odm_xsd")

    if not xml_path.exists():
        raise FileNotFoundError(f"Input ODM-XML not found at: {xml_path}")
    if xsd_path:
        validate_xml_against_xsd(xml_path, Path(xsd_path))

    metadata = parse_metadata(xml_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Metadata written to {out_path}")


if __name__ == "__main__":
    main()

## -- End of Program Code -- ##	