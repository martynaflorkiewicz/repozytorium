import sqlite3
import time

DB = "queue.db"
CHECK_INTERVAL = 5
TASK_DURATION = 30

while True:
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    SELECT id FROM tasks
    WHERE status = 'pending'
    ORDER BY created_at
    LIMIT 1
    """)
    row = cur.fetchone()

    if row:
        task_id = row[0]
        print(f"Start zadania {task_id}")

        cur.execute(
            "UPDATE tasks SET status = 'in_progress' WHERE id = ?",
            (task_id,)
        )
        conn.commit()

        time.sleep(TASK_DURATION)

        cur.execute(
            "UPDATE tasks SET status = 'done' WHERE id = ?",
            (task_id,)
        )
        conn.commit()
        print(f"Zakończono zadanie {task_id}")

    conn.close()
    time.sleep(CHECK_INTERVAL)
