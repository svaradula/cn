from audit_logger import log_user_activity

try:
    with open("audit/public/users.txt", "r") as log:
        for line in log:
            # break line with delimiter ","
            user_info = line.strip().split(",")
            log_user_activity(user_info[0], user_info[1], user_info[2])
except FileNotFoundError as e:
    print("File not found!")
    print("Filename :", e.filename)
    log_user_activity("system", "read_users_file", "failure")