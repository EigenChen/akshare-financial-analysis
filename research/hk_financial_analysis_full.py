from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "core/hk/financial_analysis_full.py"), run_name="__main__")
