"""Allow `python -m epac_viz ...` after installing the EPAC package.

Example (from the epac directory):
    python3 -m epac_viz H2O --svg
"""
from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
