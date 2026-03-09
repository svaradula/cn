# list — Ordered, mutable, allows duplicates

# List of user actions in a session
user_actions = [
    "LOGIN",
    "VIEW_DASHBOARD",
    "CLICK_REPORT",
]

# User performs a new action
user_actions.append("LOGOUT")

# Fix a wrongly logged action
user_actions[2] = "VIEW_REPORT"
user_actions.append("LOGIN")

print(user_actions)
user_actions.sort(reverse=True)
print(user_actions)


listA = [1,2,3]
listB = [4,5,6]

mixed_list = [listA, listB]
print(mixed_list[1][0])