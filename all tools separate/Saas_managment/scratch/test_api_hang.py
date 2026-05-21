import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import uvicorn
from api.main import app
import threading
import time
import requests

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8011, log_level="debug")

t = threading.Thread(target=run_server, daemon=True)
t.start()

time.sleep(3) # wait for server to start

# clear db
if os.path.exists("data/saas_spend.db"):
    os.remove("data/saas_spend.db")

print("Starting pipeline via API...")
resp = requests.post("http://127.0.0.1:8011/v1/pipeline/run")
print(resp.json())

run_id = resp.json()["run_id"]

for _ in range(15):
    time.sleep(2)
    resp = requests.get(f"http://127.0.0.1:8011/v1/pipeline/status/{run_id}")
    print("Status:", resp.json()["status"], "Current step:", resp.json()["current_step"])
