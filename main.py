"""
main.py
-------
Genie Space Catalog Migration Framework — Entry Point

Orchestrates the three-step catalog migration pipeline:
  1. Export  – fetch the Genie space from the workspace
  2. Transform – rewrite catalog/schema identifiers for target catalog
  3. Deploy  – update existing space or create a clone

Usage
-----
    python main.py

All runtime values are read from the .env file in the project root.
No command-line arguments are needed; just edit .env and run this file.
"""

import sys
import time

from config import load_config
from export_space import export_genie_space
from transform_space import transform_space
from deploy_space import deploy_space


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║        Genie Space Catalog Migration Framework               ║
║        Migrate Genie spaces between catalogs in-place        ║
╚══════════════════════════════════════════════════════════════╝
"""


def main() -> None:
    print(BANNER)

    # ------------------------------------------------------------------
    # Load and validate all environment variables
    # ------------------------------------------------------------------
    print("Loading configuration from .env ...")
    try:
        cfg = load_config()
    except EnvironmentError as exc:
        print(f"\n[FATAL] {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"  Workspace     : {cfg.host}")
    print(f"  Genie Space   : {cfg.space_id}")
    print(f"  Mode          : {cfg.migration_mode.upper()}")
    print(f"  Catalog       : {cfg.source_catalog} → {cfg.target_catalog}")
    print(f"  Target Catalog: {cfg.target_catalog}")
    if cfg.schema_map:
        print(f"  Schema map    : {cfg.schema_map}")
    if cfg.new_title:
        print(f"  New title     : {cfg.new_title}")
    print()

    start = time.time()

    # ------------------------------------------------------------------
    # Step 1 — Export
    # ------------------------------------------------------------------
    print("=" * 60)
    print("STEP 1/3 — EXPORT")
    print("=" * 60)
    exported_file = export_genie_space(cfg)
    print()

    # ------------------------------------------------------------------
    # Step 2 — Transform
    # ------------------------------------------------------------------
    print("=" * 60)
    print("STEP 2/3 — TRANSFORM")
    print("=" * 60)
    transformed_file = transform_space(exported_file, cfg)
    print()

    # ------------------------------------------------------------------
    # Step 3 — Deploy
    # ------------------------------------------------------------------
    print("=" * 60)
    print("STEP 3/3 — DEPLOY")
    print("=" * 60)
    deploy_space(transformed_file, cfg)
    print()

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    elapsed = time.time() - start
    print("=" * 60)
    print(f"[DONE] Catalog migration completed in {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
