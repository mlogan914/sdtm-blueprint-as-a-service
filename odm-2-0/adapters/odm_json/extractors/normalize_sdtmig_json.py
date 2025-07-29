import argparse
import json
from pathlib import Path
from adapters.odm_json.utils.load_paths import load_paths
from adapters.odm_json.utils.parse_sdtmig_json import extract_sdtm_metadata

def main():
    parser = argparse.ArgumentParser(
        description="Normalize SDTMIG JSON metadata from CDISC Library."
    )
    parser.add_argument("--input", help="Path to SDTMIG JSON input file")
    parser.add_argument("--output", help="Path to output normalized JSON")
    parser.add_argument("--study", type=str, help="Study ID for path resolution")
    parser.add_argument("--env", type=str, help="Environment (e.g. dev, prod)")

    args = parser.parse_args()

    # Load paths from config if --study and --env are provided
    if args.study and args.env:
        paths = load_paths(study=args.study, env=args.env)
        input_path = Path(args.input) if args.input else Path(paths["sdtmig_input_json"])
        output_path = Path(args.output) if args.output else Path(paths["sdtmig_normalized_json"])


    elif args.input and args.output:
        input_path = Path(args.input)
        output_path = Path(args.output)
    else:
        parser.error("Either --input and --output or --study and --env must be specified.")

    metadata = extract_sdtm_metadata(input_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ SDTM metadata extracted and saved to: {output_path}")

if __name__ == "__main__":
    main()

## -- End of Program Code -- ##
