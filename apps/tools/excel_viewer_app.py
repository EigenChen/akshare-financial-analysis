from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGET = ROOT / "core/tools/excel_viewer.py"


def main() -> None:
    if not TARGET.exists():
        raise FileNotFoundError(f"未找到财务分析Excel查看器主程序: {TARGET}")
    runpy.run_path(str(TARGET), run_name="__main__")


if __name__ == "__main__":
    main()
