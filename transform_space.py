"""
transform_space.py
------------------
Step 2 of the Genie Space Catalog Migration Framework.

Reads the exported Genie space JSON, rewrites all catalog/schema
identifiers and inline SQL references from source to target catalog,
and saves the transformed payload to the artifacts directory.

Transformation rules
--------------------
- ``identifier`` fields (catalog.schema.object format):
    catalog part : SOURCE_CATALOG → TARGET_CATALOG
    schema part  : mapped via SCHEMA_MAP (e.g., source_schema → target_schema)
- ``sql`` fields (string or list-of-string):
    All occurrences of SOURCE_CATALOG are replaced with TARGET_CATALOG.

All configuration is read from the Config object (populated via .env).
"""

import json
import os
import sys
from typing import Any

from config import Config


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _rewrite_identifier(identifier: str, source_catalog: str, target_catalog: str, schema_map: dict) -> str:
    """
    Rewrite a three-part ``catalog.schema.object`` identifier.

    Only identifiers that exactly match the three-part format are touched;
    anything else is returned unchanged to avoid unintended side-effects.
    """
    parts = identifier.split(".")
    if len(parts) != 3:
        return identifier  # not a fully-qualified identifier – leave as-is

    catalog, schema, obj = parts
    catalog = catalog.replace(source_catalog, target_catalog)
    schema  = schema_map.get(schema, schema)   # use mapped name, or keep original
    return f"{catalog}.{schema}.{obj}"


def _rewrite_sql(sql_val: Any, source_catalog: str, target_catalog: str) -> Any:
    """
    Replace all occurrences of SOURCE_CATALOG with TARGET_CATALOG inside a SQL value.

    The ``sql`` field in serialized Genie spaces can be either a plain string
    or a list containing a single string; both forms are handled transparently.
    """
    if isinstance(sql_val, list):
        raw = "".join(sql_val)
        replaced = raw.replace(source_catalog, target_catalog)
        return [replaced]
    return sql_val.replace(source_catalog, target_catalog)


def _walk(obj: Any, source_catalog: str, target_catalog: str, schema_map: dict, rewrites: list) -> None:
    """
    Recursively traverse the deserialized JSON object and rewrite identifiers/SQL in-place.

    Parameters
    ----------
    obj      : current node (dict, list, or scalar)
    rewrites : mutable list that accumulates log entries for the summary
    """
    if isinstance(obj, list):
        for item in obj:
            _walk(item, source_catalog, target_catalog, schema_map, rewrites)
        return

    if not isinstance(obj, dict):
        return  # scalar – nothing to do

    for key, value in obj.items():
        if key == "identifier" and isinstance(value, str):
            new_val = _rewrite_identifier(value, source_catalog, target_catalog, schema_map)
            if new_val != value:
                rewrites.append((value, new_val))
                obj[key] = new_val

        elif key == "sql" and isinstance(value, (str, list)):
            obj[key] = _rewrite_sql(value, source_catalog, target_catalog)

        else:
            _walk(value, source_catalog, target_catalog, schema_map, rewrites)


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def transform_space(in_file: str, cfg: Config) -> str:
    """
    Transform a Genie space export for the target catalog.

    Parameters
    ----------
    in_file : str
        Path to the exported JSON file (output of ``export_genie_space``).
    cfg : Config
        Fully populated configuration object loaded from environment variables.

    Returns
    -------
    str
        Absolute path to the saved transformed JSON file.

    Raises
    ------
    SystemExit
        If ``serialized_space`` is missing or cannot be parsed.
    """

    os.makedirs(cfg.out_dir, exist_ok=True)
    out_file = os.path.join(cfg.out_dir, f"{cfg.space_id}_transformed.json")

    print(f"[TRANSFORM] Rewriting catalog references...")
    print(f"            Input       : {in_file}")
    print(f"            Output      : {out_file}")
    print(f"            Catalog     : '{cfg.source_catalog}' → '{cfg.target_catalog}'")
    if cfg.schema_map:
        print(f"            Schema map  : {cfg.schema_map}")
    else:
        print(f"            Schema map  : (none – schema names unchanged)")

    # Load the exported JSON
    with open(in_file, encoding="utf-8") as f:
        space = json.load(f)

    # Deserialize the nested serialized_space string
    try:
        serialized = json.loads(space["serialized_space"])
    except (KeyError, json.JSONDecodeError) as exc:
        print(f"[ERROR] Cannot parse 'serialized_space': {exc}", file=sys.stderr)
        sys.exit(1)

    # Walk and rewrite all identifiers / SQL
    rewrites: list = []
    _walk(serialized, cfg.source_catalog, cfg.target_catalog, cfg.schema_map, rewrites)

    # Re-encode the transformed serialized_space back to a JSON string
    space["serialized_space"] = json.dumps(serialized)

    # Update title if specified
    if cfg.new_title:
        space["title"] = cfg.new_title

    # Save the transformed payload
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(space, f, indent=2)

    # Summary
    tables = serialized.get("data_sources", {}).get("tables", [])
    mvs    = serialized.get("data_sources", {}).get("metric_views", [])

    print(f"[OK] Transform complete.")
    print(f"     Identifiers rewritten : {len(rewrites)}")
    for old, new in rewrites:
        print(f"       {old}  →  {new}")
    print(f"     Tables      : {len(tables)}")
    print(f"     Metric views: {len(mvs)}")
    print(f"     Saved to    : {out_file}")

    return out_file
