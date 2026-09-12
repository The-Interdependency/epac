"""Allow `python -m viz ...` when PYTHONPATH contains the epac root.

Example (from the epac directory):
    PYTHONPATH=".:subatomic:../../libs/ucns/src" python3 -m viz H2O --svg
"""
from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
