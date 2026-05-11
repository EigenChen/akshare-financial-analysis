from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGET = ROOT / "streamlit_app.py"


def main() -> None:
    if not TARGET.exists():
        raise FileNotFoundError(f"未找到A股Streamlit主程序: {TARGET}")
    runpy.run_path(str(TARGET), run_name="__main__")


if __name__ == "__main__":
    main()
