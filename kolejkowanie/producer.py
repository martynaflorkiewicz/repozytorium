import csv
import os
from datetime import datetime
import uuid

QUEUE_FILE = "queue.csv"

def init_file():
    if not os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "status", "created_at"])

def add_task():
    task_id = str(uuid.uuid4())
    with open(QUEUE_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([task_id, "pending", datetime.now().isoformat()])
    print(f"Dodano zadanie {task_id}")

if __name__ == "__main__":
    init_file()
    add_task()
