"""Command-line entry point for reproducible Phase 3 analysis."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hk_minibus.analysis_pipeline import main

if __name__ == "__main__":
    raise SystemExit(main())
