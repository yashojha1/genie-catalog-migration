"""
export_space.py
---------------
Step 1 of the Genie Space Catalog Migration Framework.

Fetches a Genie space from the workspace via the Databricks Management
API (GET /api/2.0/genie/spaces/<id>?include_serialized_space=true) and
saves the full JSON payload to the local artifacts directory.

All configuration is read from the Config object (populated via .env).
"""

import json
import os
import sys

import requests

from config import Config


def export_genie_space(cfg: Config) -> str:
    """
    Export a Genie space from the workspace.

    Parameters
    ----------
    cfg : Config
        Fully populated configuration object loaded from environment variables.

    Returns
    -------
    str
        Absolute path to the saved JSON export file.

    Raises
    ------
    SystemExit
        On any HTTP error or missing required field in the API response.
    """

    # Determine output file path
    os.makedirs(cfg.out_dir, exist_ok=True)
    out_file = os.path.join(cfg.out_dir, f"{cfg.space_id}_export.json")

    # Build API request
    url = (
        f"{cfg.host}/api/2.0/genie/spaces/{cfg.space_id}"
        "?include_serialized_space=true"
    )
    headers = {
        "Authorization": f"Bearer {cfg.token}",
        "Content-Type":  "application/json",
    }

    print(f"[EXPORT] Fetching Genie space from workspace...")
    print(f"         URL      : {url}")

    resp = requests.get(url, headers=headers, timeout=30)

    # Surface HTTP errors clearly
    if not resp.ok:
        print(f"[ERROR] HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    space = resp.json()

    # Validate that all expected fields are present
    required_fields = ["space_id", "serialized_space", "title", "warehouse_id"]
    for field in required_fields:
        if field not in space:
            print(
                f"[ERROR] Missing field '{field}' in API response. "
                f"Check your GENIE_SPACE_ID and API permissions.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Persist the raw export
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(space, f, indent=2)

    # Print a human-readable summary
    serialized = json.loads(space["serialized_space"])
    tables   = serialized.get("data_sources", {}).get("tables", [])
    mvs      = serialized.get("data_sources", {}).get("metric_views", [])

    print(f"[OK] Export complete.")
    print(f"     Space ID    : {space['space_id']}")
    print(f"     Title       : {space['title']}")
    print(f"     Warehouse   : {space['warehouse_id']}")
    print(f"     Tables      : {len(tables)}")
    print(f"     Metric views: {len(mvs)}")
    print(f"     Saved to    : {out_file}")

    return out_file
