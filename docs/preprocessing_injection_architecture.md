# Preprocessing Injection Architecture Decisions

## Overview

The preprocessing layer is intended to support domain-level source shaping prior to scaffold generation and downstream derivation injection.

The goal is to provide a stable preprocessing contract that allows:

- Joins
- Appends
- Filtering
- Normalization
- Source consolidation

to occur before the scaffolded SDTM transformation logic executes.

This layer is intentionally separated from variable-level derivation injection architecture.

---

# Updated Folder Structure

## Custom Overrides Structure

```text
overrides/
└── custom/
    └── <domain>/
        ├── prep/
        │   └── prep_input.sql
        │
        └── derivations/
            ├── derive_age.sql
            ├── derive_race.sql
            └── ...
```

Example:

```text
overrides/custom/dm/prep/prep_input.sql
overrides/custom/dm/derivations/derive_age.sql
```

---

# Architectural Separation

## prep/

Responsible for:

- Input preprocessing
- Source shaping
- Joins
- Appends
- Harmonization
- Reusable upstream logic

This operates at the domain/input level.

---

## derivations/

Responsible for:

- Variable-level transformation injection
- SDTM derivation logic
- Sponsor-specific column logic

This operates at the variable/output level.

---

# Naming Convention Decisions

## Preprocessing File

Standardized filename:

```text
prep_input.sql
```

Rationale:

- Describes architectural purpose rather than SQL implementation detail
- Avoids over-coupling architecture to CTE terminology
- Allows future flexibility beyond pure CTE usage

---

## Final Preprocessing Output Contract

The preprocessing layer must ultimately expose:

```text
<domain>_input
```

Examples:

```text
dm_input
ae_input
ex_input
```

The scaffold generator will use this as the downstream source if preprocessing exists.

---

# Scaffold Generator Behavior

## If prep_input.sql exists

The scaffold generator should:

1. Detect:
   ```text
   overrides/custom/<domain>/prep/prep_input.sql
   ```

2. Inject preprocessing SQL before scaffold SELECT logic

3. Use:
   ```sql
   FROM <domain>_input
   ```

4. Continue downstream derivation injection normally

---

## If prep_input.sql does NOT exist

Fallback behavior:

```sql
FROM {{ ref('raw_<domain>') }}
```

Example:

```sql
FROM {{ ref('raw_dm') }}
```

---

# Internal Preprocessing Design

The preprocessing file may contain multiple internal CTEs and transformation steps.

Example:

```sql
WITH

dm_demog AS (
    SELECT *
    FROM {{ ref('raw_dm_demog') }}
),

dm_append AS (
    SELECT *
    FROM {{ ref('raw_dm_append') }}
),

dm_joined AS (
    SELECT *
    FROM dm_demog
),

dm_input AS (
    SELECT *
    FROM dm_joined
    UNION ALL
    SELECT *
    FROM dm_append
)
```

The important architectural requirement is NOT how preprocessing is implemented internally.

The important requirement is:

```text
prep_input.sql must ultimately expose <domain>_input
```

---

# Architectural Rationale

The preprocessing layer provides:

- Stable downstream scaffold interfaces
- Reusable preprocessing logic
- Modular source orchestration
- Separation of preprocessing from derivation behavior
- Simplified scaffold generation logic
- Future extensibility

This architecture intentionally avoids requiring the scaffold engine to understand:

- Joins
- Appends
- Ordering logic
- Harmonization logic
- Source complexity

The scaffold engine only needs to know:

```text
Does preprocessing exist?
If yes:
    use <domain>_input
Else:
    use default raw source
```

---

# Design Decisions

## Decision: Single Preprocessing Entry Point Per Domain

Current direction:

```text
One prep_input.sql file per domain
```

Rationale:

- Keeps scaffold logic simple
- Avoids dependency ordering complexity
- Avoids orchestration graph requirements
- Avoids multiple preprocessing execution stages
- Supports most realistic preprocessing scenarios
