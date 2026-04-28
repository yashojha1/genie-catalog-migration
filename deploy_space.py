"""
deploy_space.py
---------------
Step 3 of the Genie Space Catalog Migration Framework.

Reads the transformed Genie space JSON and deploys it back to the
workspace via the Management API.

Deployment behaviour
--------------------
- If ``MIGRATION_MODE`` is "update" → Updates the existing space (PATCH).
- If ``MIGRATION_MODE`` is "clone" → Creates a new Genie space (POST).

After a successful clone, the console prints the new Space ID.

All configuration is read from the Config object (populated via .env).
"""

import json
import os
import sys

import requests

from config import Config


def deploy_space(in_file: str, cfg: Config) -> None:
    """
    Deploy (update existing or clone) a Genie space in the workspace.

    Parameters
    ----------
    in_file : str
        Path to the transformed JSON file (output of ``transform_space``).
    cfg : Config
        Fully populated configuration object loaded from environment variables.

    Raises
    ------
    SystemExit
        On any HTTP error from the workspace API.
    """

    headers = {
        "Authorization": f"Bearer {cfg.token}",
        "Content-Type":  "application/json",
    }

    # -----------------------------------------------------------------------
    # Load the transformed payload
    # -----------------------------------------------------------------------
    with open(in_file, encoding="utf-8") as f:
        space = json.load(f)

    # Build the deployment payload
    payload = {
        "title":            space.get("title", "Genie Space"),
        "description":      space.get("description", "Migrated to new catalog via CI/CD pipeline"),
        "warehouse_id":     cfg.warehouse_id,
        "serialized_space": space["serialized_space"],
    }

    # -----------------------------------------------------------------------
    # Create (POST) or Update (PATCH)
    # -----------------------------------------------------------------------
    if cfg.migration_mode == "update":
        # ---- UPDATE existing space ----------------------------------------
        url = f"{cfg.host}/api/2.0/genie/spaces/{cfg.space_id}"
        print(f"[DEPLOY] Updating existing Genie space (catalog migration)...")
        print(f"         URL      : {url}")
        resp = requests.patch(url, headers=headers, json=payload, timeout=30)
    else:
        # ---- CLONE: Create new space --------------------------------------
        # Ensure parent folder exists
        mkdirs_url = f"{cfg.host}/api/2.0/workspace/mkdirs"
        mkdirs_resp = requests.post(
            mkdirs_url,
            headers=headers,
            json={"path": cfg.parent_path},
            timeout=30,
        )
        if not mkdirs_resp.ok:
            print(
                f"[WARN] Could not create parent path '{cfg.parent_path}': "
                f"{mkdirs_resp.text}",
                file=sys.stderr,
            )

        # Add title suffix for cloned spaces
        payload["title"] = payload["title"] + cfg.title_suffix
        payload["parent_path"] = cfg.parent_path

        url = f"{cfg.host}/api/2.0/genie/spaces"
        print(f"[DEPLOY] Creating new Genie space (clone mode)...")
        print(f"         URL      : {url}")
        resp = requests.post(url, headers=headers, json=payload, timeout=30)

    # -----------------------------------------------------------------------
    # Handle the response
    # -----------------------------------------------------------------------
    if not resp.ok:
        print(f"[ERROR] HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    result = resp.json()

    print(f"[OK] Deployment successful!")
    print(f"     Space ID  : {result.get('space_id')}")
    print(f"     Title     : {result.get('title')}")
    print(f"     Warehouse : {result.get('warehouse_id')}")

    # If this was a clone, remind the user to save the new Space ID
    if cfg.migration_mode == "clone":
        print()
        print("━" * 60)
        print("ACTION — Save the new Space ID for future reference:")
        print(f"  New Space ID: {result.get('space_id')}")
        print("  Update your documentation or bookmarks with this ID.")
        print("━" * 60)
