# Genie Space Catalog Migration Framework

A VS Code project for migrating Databricks Genie spaces between catalogs **within the same workspace**. This tool automatically updates all catalog and schema references in your Genie space configuration.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [VS Code Integration](#vs-code-integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

This framework automates migrating a Genie space from one catalog to another within the same Databricks workspace:

```
Before: genie_space uses catalog_a.bronze, catalog_a.silver, catalog_a.gold
                         │
                         ▼
              Run: python main.py
                         │
                         ▼
After:  genie_space uses catalog_b.bronze, catalog_b.silver, catalog_b.gold
```

### Use Cases

- **Catalog consolidation** - Merge data from multiple catalogs into one
- **Environment promotion** - Move from dev catalog to prod catalog
- **Data migration** - Switch Genie spaces to new catalog structure
- **Testing** - Clone a space to test against a different catalog

---

## Features

- **Same-workspace migration** - Optimized for single-workspace catalog changes
- **Dynamic configuration** - All settings via `.env` file, no code changes
- **Schema mapping** - Optionally remap schema names during migration
- **Two modes**:
  - `update` - Modify the existing space in-place
  - `clone` - Create a new copy pointing to the target catalog
- **SQL rewriting** - Automatically updates all SQL queries
- **Identifier rewriting** - Updates table and metric view references
- **VS Code ready** - Pre-configured debug and task configurations
- **Artifact generation** - JSON exports for review and auditing

---

## Prerequisites

- **Python 3.8+** installed
- **VS Code** with Python extension (recommended)
- **Databricks workspace** with:
  - `CAN_MANAGE` permission on the Genie space
  - Access to both source and target catalogs
- **Personal Access Token** with appropriate permissions

---

## Installation

### Step 1: Navigate to Project

```bash
cd genie-catalog-migration
```

### Step 2: Create Virtual Environment

```bash
# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Create Environment File

```bash
cp .env.example .env
```

---

## Configuration

Open `.env` and configure the following:

### Workspace Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABRICKS_HOST` | Workspace URL | `https://dbc-xxxx.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | Personal Access Token | `dapiXXXXXXXX` |
| `DATABRICKS_WAREHOUSE_ID` | SQL Warehouse for Genie | `abc123xyz` |

### Genie Space Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `GENIE_SPACE_ID` | Space to migrate | `a1b2c3d4...` (32 chars) |
| `NEW_TITLE` | Optional new title | `My Migrated Space` |

### Catalog Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `SOURCE_CATALOG` | Current catalog | `analytics_dev` |
| `TARGET_CATALOG` | Target catalog | `analytics_prod` |
| `SCHEMA_MAP` | Schema remapping | `dev:prod,bronze:gold` |

### Deployment Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MIGRATION_MODE` | `update` or `clone` | `update` |
| `PARENT_PATH` | Workspace folder (clone mode) | `/Workspace/Genie/Migrated` |
| `TITLE_SUFFIX` | Suffix for cloned spaces | ` [Migrated]` |

---

## Usage

### Full Migration Pipeline

```bash
python main.py
```

This runs all three steps:
1. **Export** - Downloads the Genie space JSON
2. **Transform** - Rewrites catalog/schema references
3. **Deploy** - Updates or clones the space

### Migration Modes

#### Update Mode (Default)

Modifies the existing Genie space to point to the new catalog:

```bash
# In .env
MIGRATION_MODE=update
```

#### Clone Mode

Creates a new Genie space copy with the new catalog:

```bash
# In .env
MIGRATION_MODE=clone
```

After cloning, save the new Space ID from the output for future reference.

### Example Scenarios

#### Scenario 1: Dev to Prod Catalog

```env
GENIE_SPACE_ID=abc123...
SOURCE_CATALOG=analytics_dev
TARGET_CATALOG=analytics_prod
MIGRATION_MODE=update
```

#### Scenario 2: Clone for Testing

```env
GENIE_SPACE_ID=abc123...
SOURCE_CATALOG=analytics_prod
TARGET_CATALOG=analytics_test
MIGRATION_MODE=clone
NEW_TITLE=Analytics (Test Copy)
```

#### Scenario 3: With Schema Remapping

```env
SOURCE_CATALOG=legacy
TARGET_CATALOG=unified
SCHEMA_MAP=sales:sales_2024,marketing:growth_marketing
```

---

## VS Code Integration

### Launch Configurations (F5)

| Configuration | Description |
|---------------|-------------|
| **Run Catalog Migration** | Run full pipeline with debugging |
| **Debug: Export Space** | Debug only the export step |
| **Debug: Transform Space** | Debug only the transform step |
| **Debug: Deploy Space** | Debug only the deploy step |

### Tasks (Ctrl+Shift+B)

| Task | Description |
|------|-------------|
| **Run Catalog Migration** | Default build task |
| **Setup Virtual Environment** | Create venv and install deps |
| **Install Dependencies** | Reinstall requirements |
| **Copy .env.example to .env** | Create local config |
| **Clean Artifacts** | Remove exported JSON files |
| **Validate Configuration** | Check .env is valid |

### Recommended Extensions

- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Black Formatter** (ms-python.black-formatter)
- **DotENV** (mikestead.dotenv)

---

## Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid/expired token | Regenerate at `/user-settings/tokens` |
| `404 Not Found` | Invalid space ID | Check URL for 32-char hex ID |
| `Catalog does not exist` | Target catalog missing | Create catalog first |
| `Permission denied` | Insufficient access | Request `CAN_MANAGE` on space |
| `ModuleNotFoundError` | Dependencies missing | Run `pip install -r requirements.txt` |

### Finding IDs

**Genie Space ID:**
```
https://<workspace>.cloud.databricks.com/genie/spaces/<SPACE_ID_HERE>
```

**Warehouse ID:**
```
https://<workspace>.cloud.databricks.com/sql/warehouses/<WAREHOUSE_ID_HERE>
```

### Verifying Migration

After migration, verify by:
1. Opening the Genie space in the workspace
2. Checking that tables point to the new catalog
3. Running a few questions to confirm SQL executes correctly

---

## Project Structure

```
genie-catalog-migration/
├── .vscode/
│   ├── launch.json          # Debug configurations
│   ├── settings.json        # Python/linting settings
│   └── tasks.json           # Build tasks
├── artifacts/               # Exported JSON files
├── .env                     # Your configuration (gitignored)
├── .env.example             # Template for .env
├── .gitignore               # Git ignore rules
├── config.py                # Environment loading
├── deploy_space.py          # Step 3: Deploy
├── export_space.py          # Step 1: Export
├── main.py                  # Entry point
├── transform_space.py       # Step 2: Transform
├── requirements.txt         # Dependencies
└── README.md                # This file
```

---

## Security Notes

- **Never commit `.env`** - Contains sensitive tokens
- **Rotate tokens regularly** - Especially after team changes
- **Use minimal permissions** - Only grant required access
- **Review artifacts** - JSON files may contain sensitive metadata

---

## Support

- **Databricks Genie API Docs**: https://docs.databricks.com/en/genie/conversation-api
- **Issues**: Check the Troubleshooting section or review `config.py` for validation logic
