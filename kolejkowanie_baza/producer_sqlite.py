import sqlite3
import uuid
from datetime import datetime

DB = "queue.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    status TEXT,
    created_at TEXT
)
""")

task_id = str(uuid.uuid4())

cur.execute(
    "INSERT INTO tasks VALUES (?, ?, ?)",
    (task_id, "pending", datetime.now().isoformat())
)

conn.commit()
conn.close()

print(f"Dodano zadanie {task_id}")
