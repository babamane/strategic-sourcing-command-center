import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from api.pipeline_state import get_latest_run
import json
from dataclasses import asdict

run = get_latest_run()
if run:
    print(json.dumps(asdict(run), indent=2))
else:
    print("No runs found.")
