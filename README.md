# SDTM Blueprint‑as‑a‑Service (BaaS)

> ⚠️ **Project Status:** This repository is under active development. Expect ongoing refactoring, feature additions, and changes until the first stable release.

Metadata‑driven scaffolding and reproducible pipelines for SDTM domain production, powered by ODM‑XML/JSON, dbt, and modern data‑platform patterns.

> **Goal:** Turn clinical‑trial metadata into working SDTM models with minimal hand‑coding by generating domain scaffolds, injecting standard/custom derivations, and orchestrating end‑to‑end runs across studies.

---

## Table of contents
- [Concept](#concept)
- [Repo layout](#repo-layout)
- [Quick start](#quick-start)
- [Detailed workflow](#detailed-workflow)
- [Commands & scripts](#commands--scripts)
- [Configuration](#configuration)
- [Conventions](#conventions)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [License](#license)

---

## Concept
**Blueprint‑as‑a‑Service** treats SDTM production as a *templateable platform*: metadata (ODM + SDTMIG reference) defines what to build; adapters convert that metadata into normalized JSON; a scaffolder generates dbt SQL per domain; and small override files insert standard or study‑specific derivations. A thin runner coordinates per‑study runs.

**Key ideas**
- Use **ODM‑XML/JSON** as the single source of truth for CRF/Item metadata.
- Normalize/compare metadata to **SDTMIG** references to determine mappings and derivations.
- **Generate** dbt models per domain and **inject** custom SQL fragments when needed.
- Run locally with **DuckDB** or point dbt at your warehouse for the same compiled output.

---

## Repo layout
> High‑level folders you’ll use most often.

```
./
├─ odm-2-0/                 # Root for ODM v2 adapter + pipelines
│  ├─ adapters/odm_json/    # Adapter code to parse/normalize ODM JSON
│  ├─ ref/                  # SDTM IG / reference JSON and helpers
│  └─ tools/                # Matching, extraction, utilities
├─ studies/
│  └─ VEXIN-03/             # Example study: inputs, overrides, dbt project
│      ├─ inputs/           # ODM JSON, supplemental inputs
│      ├─ overrides/        # custom SQL fragments per domain/variable
│      │   └─ custom/
│      │       └─ dm/derive_dmdtc.sql  # example override
│      └─ dbt/              # dbt project (models/sdtm/, macros, tests)
├─ ref/                     # Top-level reference (mirrors or links to odm-2-0/ref)
├─ run_baas.sh              # Entry script to run end‑to‑end for a study/domain
└─ scripts/                 # CLIs: extract, match, scaffold, validate
```

> **Note:** If you reorganize, keep the separation between **adapters**, **reference**, **study assets**, and **runners**. The scaffolder reads per‑study config and writes dbt SQL into the study’s `dbt/models/sdtm/`.

---

## Quick start
### Prereqs
- **Python 3.11+**
- **dbt-core** (DuckDB profile for local quick runs) and **DuckDB**
- **poetry** or **pip + venv**

```bash
# clone
git clone https://github.com/mlogan914/sdtm-blueprint-as-a-service.git
cd sdtm-blueprint-as-a-service

# (optional) create venv
python -m venv .venv && source .venv/bin/activate

# install python deps
pip install -r requirements.txt  # or: poetry install

# set up dbt (DuckDB)
cd studies/VEXIN-03/dbt
# add a duckdb profile (see profiles.yml example below)
```

### One‑command demo (VEXIN‑03)
```bash
# from repo root
./run_baas.sh studies/VEXIN-03 dm  # scaffold & run DM for sample study VEXIN‑03
```
This will:
1) parse/normalize the study’s ODM JSON, 2) match to SDTM reference, 3) scaffold dbt SQL for the domain, 4) inject overrides (if any), and 5) `dbt run` against DuckDB.

---

## Detailed workflow
1. **Extract & normalize ODM**
   - Convert ODM‑XML → normalized JSON (adapter under `odm-2-0/adapters/odm_json/`).
2. **Match to SDTM reference**
   - Compare normalized ItemOIDs/Names to SDTMIG variable catalog; mark mapping type:
     - *direct* (1:1), *standard‑derived* (macro/known calc), *custom* (needs override), *suppqual* (SUPPxx).
3. **Scaffold dbt SQL**
   - Generate `studies/<study>/dbt/models/sdtm/<domain>.sql` with jinja slots for derivations.
4. **Inject derivations**
   - Insert snippets from `studies/<study>/overrides/custom/<domain>/derive_<var>.sql` into the scaffold.
5. **Run dbt**
   - Target DuckDB for local dev; same SQL can target Snowflake/Redshift/etc.
6. **Validate**
   - (Planned) automated checks & tests under `dbt/tests/` and custom validators.

---

## Commands & scripts
> Names may differ slightly depending on your local branch; the runner wires them together.

- `run_baas.sh <study_dir> <domain>` — end‑to‑end run for a given study and domain.
- `extract_odm_json.py` — parse ODM‑XML → normalized JSON.
- `match_odm_to_sdtm.py` — produce a mapping CSV/JSON (with `Mapping_Type`, `Derived_Target`, etc.).
- `scaffold_sql.py` — generate dbt SQL from the mapping output; insert jinja placeholders.
- `inject_overrides.py` — post‑process scaffolded SQL to inject `overrides/custom/<domain>/derive_*.sql`.
- `tools/` utilities — macros (e.g., date conversion), helpers, and CLI glue.

### Example
```bash
# extract & match
python odm-2-0/adapters/odm_json/extract_odm_json.py \
  --odm-xml studies/VEXIN-03/inputs/odm.xml \
  --out studies/VEXIN-03/inputs/odm.json

python odm-2-0/tools/match_odm_to_sdtm.py \
  --odm-json studies/VEXIN-03/inputs/odm.json \
  --ref odm-2-0/ref/sdtmig.json \
  --out studies/VEXIN-03/outputs/mapping.csv

# scaffold & inject
python scripts/scaffold_sql.py \
  --mapping studies/VEXIN-03/outputs/mapping.csv \
  --domain DM \
  --out studies/VEXIN-03/dbt/models/sdtm/DM.sql

python scripts/inject_overrides.py \
  --domain DM \
  --overrides studies/VEXIN-03/overrides/custom/dm \
  --model studies/VEXIN-03/dbt/models/sdtm/DM.sql

# run dbt
cd studies/VEXIN-03/dbt && dbt run --select sdtm.DM
```

---

## Configuration
### dbt profiles example (DuckDB)
`~/.dbt/profiles.yml`
```yaml
vexin03:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: /tmp/vexin03.duckdb
      threads: 4
```
Then in `studies/VEXIN-03/dbt/dbt_project.yml` set `profile: vexin03`.

### Study structure
```text
studies/<STUDY_ID>/
  inputs/               # odm.xml, odm.json, supplemental
  outputs/              # mapping artifacts, logs
  overrides/
    custom/<domain>/
      derive_<var>.sql  # injected fragments
  dbt/
    models/sdtm/       # generated models
    macros/            # e.g., convert_us_to_iso8601.sql
    tests/             # optional
```

### Mapping CSV fields (typical)
- `ItemOID`, `Name`, `SDTM_Var`, `Mapping_Type` (direct | standard_derived | custom | suppqual),
- `Derived_Target`, `SDTM_Label`, `CodeList`, `SDTM_Path`, `Notes`.

---

## Conventions
- **Domains** are uppercase (e.g., DM, AE). Override folders are lowercase (`dm`, `ae`).
- **Derivation files** are `derive_<var>.sql`; one variable per file keeps diffs clean.
- **Macros** live under the study dbt project (e.g., `macros/convert_us_to_iso8601.sql`).
- **Idempotent scaffolding** — re‑runs should overwrite in place without manual cleanup.

---

## Roadmap
- ☑️ DuckDB local profile and first end‑to‑end dbt run
- ☑️ Injection of standard/custom derivations via per‑var SQL fragments
- ☐ Multi‑domain runs (loop in runner)
- ☐ SUPPQUAL generation helper
- ☐ Automated tests/validators (schema + content checks)
- ☐ Warehouse targets (Snowflake/Redshift/BigQuery) via dbt profiles
- ☐ CLI packaging (pipx/poetry) + `baas` command
- ☐ GitHub Actions CI for lint + unit tests + sample run artifacts

---

## FAQ
**Is this production‑ready?**  
Not yet. It’s a working blueprint under active development. Expect refactors and interface changes.

**Can I run all domains at once?**  
Yes in principle — extend `run_baas.sh` to iterate over a domain list or detect needed domains from the mapping output.

**Where do date/format conversions live?**  
Use dbt macros in the study project (e.g., `convert_us_to_iso8601.sql`), referenced by generated SQL or overrides.

**What if ItemDef `Name` ≠ the OID suffix?**  
The matcher handles the `Name` vs `OID` discrepancy and records the resolved target variable; check the mapping CSV before scaffolding.

<!-- ---

## License
MIT (or your chosen permissive license). Add a LICENSE file at repo root. -->
