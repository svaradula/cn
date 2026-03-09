from datetime import datetime
import os

LOG_DIR = "clases/logs"

def log_account_activity(account_no, action, status):
    print(f"Logging activity: Account={account_no}, Action={action}, Status={status}")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_path = os.path.join(LOG_DIR, "account_activity.log")
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} | Account: {account_no} | Action: {action} | Status: {status}\n"

    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
            print("Activity logged successfully.")
    except Exception as e:
        print("❌ Failed to write to account log:", e)