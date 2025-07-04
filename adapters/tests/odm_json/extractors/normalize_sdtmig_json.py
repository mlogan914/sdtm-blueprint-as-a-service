import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.parse_sdtmig_json import extract_sdtm_metadata

def main():
    parser = argparse.ArgumentParser(
        description="Extract SDTM reference metadata from CDISC Library JSON export."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to SDTMIG JSON file from CDISC Library"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to save flattened SDTM metadata JSON"
    )
    args = parser.parse_args()

    metadata = extract_sdtm_metadata(args.input)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ SDTM metadata extracted and saved to: {args.output}")

if __name__ == "__main__":
    main()
    
## -- End of Program Code -- ##