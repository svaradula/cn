from datetime import datetime
import os

LOG_DIR = "audit/files"
LOG_FILE = "user_activity.log"

def log_user_activity(user_id, action, status):
    print(f"Logging activity: User={user_id}, Action={action}, Status={status}")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_path = os.path.join(LOG_DIR, LOG_FILE)
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} | User: {user_id} | Action: {action} | Status: {status}\n"

    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
            print("Activity logged successfully.")
    except Exception as e:
        print("❌ Failed to write to audit log:", e)