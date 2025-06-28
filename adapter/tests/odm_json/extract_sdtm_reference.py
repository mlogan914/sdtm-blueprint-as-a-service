import argparse
import json
from utils.extract_sdtm_metadata import extract_sdtm_metadata

def main():
    parser = argparse.ArgumentParser(description="Extract SDTM reference metadata from CDISC Library JSON export.")
    parser.add_argument("input_json", help="Path to SDTMIG JSON file from CDISC Library")
    parser.add_argument("output_json", help="Path to save flattened SDTM metadata JSON")
    args = parser.parse_args()

    metadata = extract_sdtm_metadata(args.input_json)

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ SDTM metadata extracted and saved to {args.output_json}")

if __name__ == "__main__":
    main()
