"""
config.py
---------
Loads all environment variables from the .env file and exposes them
as a typed Config object used across all modules.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file from the project root (same directory as this file)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


def _require(key: str) -> str:
    """Read a required env var; raise a clear error if missing or empty."""
    val = os.getenv(key, "").strip()
    if not val:
        raise EnvironmentError(
            f"[CONFIG] Required environment variable '{key}' is missing or empty. "
            f"Check your .env file."
        )
    return val


def _optional(key: str, default: str = "") -> str:
    """Read an optional env var with a fallback default."""
    return os.getenv(key, default).strip()


@dataclass(frozen=True)
class Config:
    """Configuration for Genie Space Catalog Migration."""

    # Workspace
    host: str
    token: str
    warehouse_id: str

    # Genie Space
    space_id: str
    new_title: str  # empty = keep original

    # Catalog migration
    source_catalog: str
    target_catalog: str

    # Schema mapping (parsed dict)
    schema_map: dict

    # Deployment settings
    migration_mode: str  # "update" or "clone"
    parent_path: str
    title_suffix: str

    # Artifact storage
    out_dir: str


def load_config() -> Config:
    """Parse and validate all environment variables, return a Config instance."""

    # Parse SCHEMA_MAP string  →  {"source_schema": "target_schema", ...}
    schema_map_str = _optional("SCHEMA_MAP", "")
    schema_map: dict = {}
    for pair in schema_map_str.split(","):
        if ":" in pair:
            k, v = pair.strip().split(":", 1)
            schema_map[k.strip()] = v.strip()

    # Validate migration mode
    mode = _optional("MIGRATION_MODE", "update").lower()
    if mode not in ("update", "clone"):
        raise EnvironmentError(
            f"[CONFIG] MIGRATION_MODE must be 'update' or 'clone', got: '{mode}'"
        )

    return Config(
        # Workspace
        host        = _require("DATABRICKS_HOST").rstrip("/"),
        token       = _require("DATABRICKS_TOKEN"),
        warehouse_id= _require("DATABRICKS_WAREHOUSE_ID"),

        # Genie Space
        space_id    = _require("GENIE_SPACE_ID"),
        new_title   = _optional("NEW_TITLE", ""),

        # Catalog migration
        source_catalog = _require("SOURCE_CATALOG"),
        target_catalog = _require("TARGET_CATALOG"),

        # Schema mapping
        schema_map  = schema_map,

        # Deployment
        migration_mode = mode,
        parent_path = _optional("PARENT_PATH", "/Workspace/Genie/Migrated"),
        title_suffix = _optional("TITLE_SUFFIX", " [Migrated]"),

        # Artifact storage
        out_dir     = _optional("OUT_DIR", "./artifacts"),
    )
