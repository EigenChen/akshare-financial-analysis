from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "tests/测试接口_查找可用方法.py"), run_name="__main__")
