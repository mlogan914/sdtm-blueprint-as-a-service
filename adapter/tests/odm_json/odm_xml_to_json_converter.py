import xml.etree.ElementTree as ET
import json
import argparse
from pathlib import Path
from lxml import etree

NS = {"odm": "http://www.cdisc.org/ns/odm/v2.0"}


# -- Schema Validation
def validate_xml_against_xsd(xml_path: Path, xsd_path: Path):
    """Validate the XML against a given XSD schema."""
    with open(xsd_path, 'rb') as f:
        schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)

    xml_doc = etree.parse(str(xml_path))
    is_valid = schema.validate(xml_doc)

    if not is_valid:
        raise ValueError(f"XML validation failed:\n{schema.error_log}")
    print(f"✅ XML file {xml_path.name} is valid against {xsd_path.name}")

# -- XML Parse
def parse_metadata(xml_path: Path) -> dict:
    """Extract Study‑level MetaDataVersion information (forms, item groups, items,
    and codelists) from an ODM‑XML file. ClinicalData are ignored."""

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
        description="Extract ODM-XML metadata (MetaDataVersion) and output as JSON.")
    parser.add_argument("--input", "-i", required=True, help="Path to ODM-XML file")
    parser.add_argument("--output", "-o", help="Destination JSON path")
    parser.add_argument("--xsd", help="Optional path to XSD for schema validation")
    args = parser.parse_args()

    inp = Path(args.input)
    outp = Path(args.output) if args.output else inp.with_name(inp.stem + "_metadata.json")

    if not inp.exists():
        raise FileNotFoundError(f"Input file {inp} not found")

    if args.xsd:
        validate_xml_against_xsd(inp, Path(args.xsd))

    metadata_json = parse_metadata(inp)
    with open(outp, "w", encoding="utf-8") as fh:
        json.dump(metadata_json, fh, indent=2)

    print(f"✅ JSON written to {outp}")

if __name__ == "__main__":
    main()

## -- End of Program Code --##