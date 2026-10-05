"""Run the shared review verification with axe installed by the readability workflow."""
import os,runpy
from pathlib import Path
os.environ['MAKEGOOD_REPORT']='readability-live'
runpy.run_path(str(Path(__file__).with_name('verify-makegood.py')),run_name='__main__')
