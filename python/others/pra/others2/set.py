# set — Unordered, mutable, unique values

# Active users in a system
active_users = {"user1", "user2", "user3", "user3", "user1"}

# Duplicate login attempt
active_users.add("user2")  # No effect

# New user logs in
active_users.add("user4")

print(active_users)

if "user3" in active_users:
    print("User3 is online")
