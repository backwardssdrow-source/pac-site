"""Run the shared accessibility and navigation checks."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("verify-makegood-accessibility.py")), run_name="__main__")
