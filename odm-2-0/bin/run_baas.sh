#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=.

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <STUDY_ID> [ENV]"
  echo "Example: $0 VEXIN-03 dev"
  exit 1
fi

STUDY="$1"
ENV="${2:-dev}"

ROOT_DIR=$(pwd)
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_DIR="$ROOT_DIR/studies/$STUDY/runs/logs"
LOG_FILE="$LOG_DIR/pipeline.log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "[$(date)] Starting pipeline for study: $STUDY (env=$ENV)"

DOMAIN_LIST=("DM")  # Add more like "AE" "VS" etc.

echo "Step 1: Convert ODM-XML to JSON"
python3 -m adapters.odm_json.extractors.convert_odm_xml_to_json \
  --study "$STUDY" \
  --env "$ENV"

echo "Step 2: Normalize SDTMIG JSON"
python3 -m adapters.odm_json.extractors.normalize_sdtmig_json \
  --study "$STUDY" \
  --env "$ENV"

echo "Step 3: Match ODM to SDTM"
python3 -m adapters.odm_json.matchers.match_odm_to_sdtm \
  --study "$STUDY" \
  --env "$ENV"

echo "Step 4: Scaffold SQL per domain"
for DOMAIN in "${DOMAIN_LIST[@]}"; do
  echo "  → Scaffolding domain: $DOMAIN"
  python3 -m adapters.odm_json.scaffolds.scaffold_sql \
    --study "$STUDY" \
    --env "$ENV" \
    --domain "$DOMAIN"
done

echo "[$(date)] Pipeline completed for study: $STUDY"
echo "Logs saved to: $LOG_FILE"

## -- End of Program Script -- ##