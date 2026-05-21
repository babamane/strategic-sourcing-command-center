import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from api.pipeline_state import create_run
from api.routers.pipeline import _execute_pipeline
from db.connection import get_database_path
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

run = create_run()
_execute_pipeline(run)

print(run.status)
print(run.failure_summary)
