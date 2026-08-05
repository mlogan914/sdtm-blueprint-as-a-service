# BaaS CI/CD Roadmap

## Phase 1 -- CI Foundation ✅

**Goal:** Validate that the project is healthy before executing the
pipeline.

### Workflow

-   Trigger on:
    -   `push`
    -   `pull_request`
    -   `workflow_dispatch`

### Job: `validate`

Responsibilities:

1.  Check out repository
2.  Set up Python
3.  Install dependencies
4.  Check Python syntax
5.  Validate shell script syntax
6.  Create a temporary dbt profile on the runner
7.  Run `dbt parse`
8.  Run `dbt compile`

**Purpose:** Catch syntax and configuration problems as early as
possible.

------------------------------------------------------------------------

## Phase 2 -- Integration Testing ✅

**Goal:** Verify that the application actually works.

### Job: `integration-test`

Depends on:

``` yaml
needs: validate
```

Because every job runs on a fresh GitHub runner, this job must repeat
its environment setup.

### Setup

1.  Checkout repository
2.  Set up Python
3.  Install dependencies
4.  Create dbt profile

### Execute

1.  `dbt seed`
2.  `dbt run`
3.  `dbt test`
4.  Verify expected outputs

Example verification ideas:

-   Expected tables exist
-   Expected row counts
-   Expected SQL generated
-   Expected files created

------------------------------------------------------------------------

## Phase 3 -- Performance Improvements

Examples:

-   Cache pip dependencies
-   Cache dbt packages
-   Upload logs on failure
-   Upload build artifacts
-   Add GitHub job summaries

------------------------------------------------------------------------

## Phase 4 -- Multiple Jobs

Split responsibilities.

``` text
BaaS CI
├── validate
└── integration-test
```

Possible future jobs:

-   lint
-   unit-test
-   integration-test
-   package
-   deploy

------------------------------------------------------------------------

## Phase 5 -- Continuous Deployment (Optional)

Possible deployment targets:

-   GitHub Pages
-   Docker image
-   Python package
-   Generated SQL artifacts

------------------------------------------------------------------------

## Phase 6 -- Production Features

Ideas:

-   Matrix builds (multiple Python versions)
-   Scheduled workflows
-   Release workflows
-   Branch protection
-   Environment protection
-   Manual approvals

------------------------------------------------------------------------

# Future Enhancement: S3 + DuckDB

Current architecture:

``` text
CSV Seeds
    ↓
DuckDB
    ↓
dbt
```

Future architecture:

``` text
S3
    ↓
DuckDB
    ↓
dbt
```

Steps:

1.  Upload synthetic data to S3.
2.  Configure GitHub OIDC.
3.  Create an AWS IAM role.
4.  Authenticate the GitHub runner.
5.  Allow DuckDB to read S3.
6.  Replace seed inputs with S3-backed sources.