import csv
import time
import os

QUEUE_FILE = "queue.csv"
CHECK_INTERVAL = 5
TASK_DURATION = 30

def read_tasks():
    with open(QUEUE_FILE, newline="") as f:
        return list(csv.DictReader(f))

def write_tasks(tasks):
    with open(QUEUE_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "status", "created_at"])
        writer.writeheader()
        writer.writerows(tasks)

def consume():
    while True:
        if not os.path.exists(QUEUE_FILE):
            time.sleep(CHECK_INTERVAL)
            continue

        tasks = read_tasks()
        for task in tasks:
            if task["status"] == "pending":
                print(f"Start zadania {task['id']}")
                task["status"] = "in_progress"
                write_tasks(tasks)

                time.sleep(TASK_DURATION)

                task["status"] = "done"
                write_tasks(tasks)
                print(f"Zakończono zadanie {task['id']}")
                break

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    consume()
