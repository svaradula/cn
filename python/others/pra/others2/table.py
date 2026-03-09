# | Type        | Real-World Meaning | Think Of           |
# | ----------- | ------------------ | ------------------ |
# | `list`      | Timeline           | Activity logs      |
# | `tuple`     | Contract           | DB rows, configs   |
# | `set`       | Crowd              | Unique users       |
# | `frozenset` | Law                | Permissions        |
# | `dict`      | Profile            | JSON / API payload |
# ---------------------------------------------------------

# | Feature           | **List**            | **Tuple**        | **Set**          | **Dictionary**        |
# | ----------------- | ------------------- | ---------------- | ---------------- | --------------------- |
# | Syntax            | `[ ]`               | `( )`            | `{ }`            | `{ key: value }`      |
# | Ordered           | ✅ Yes              | ✅ Yes            | ❌ No             | ✅ Yes *(Python 3.7+)* |
# | Mutable           | ✅ Yes               | ❌ No             | ✅ Yes            | ✅ Yes                 |
# | Allows Duplicates | ✅ Yes               | ✅ Yes            | ❌ No             | ❌ Keys only           |
# | Indexed Access    | ✅ Yes               | ✅ Yes            | ❌ No             | ❌ (key-based)         |
# | Key–Value Pair    | ❌ No                | ❌ No             | ❌ No             | ✅ Yes                 |
# | Use Case          | Collection of items | Fixed data       | Unique values    | Structured data       |
# | Performance       | Moderate            | Faster than list | Very fast lookup | Very fast lookup      |
# | Example           | `[1, 2, 2]`         | `(1, 2, 2)`      | `{1, 2}`         | `{"a": 1}`            |

# =====================================================================================================================

emails = ["a@gmail.com", "b@gmail.com", "a@gmail.com"] #list
print(type(emails))
unique_emails = set(emails) #set - to remove duplicates

print(unique_emails)
print(type(unique_emails))

muted_emails = tuple(unique_emails) #tuple - to make it immutable.
print(muted_emails)
print(type(muted_emails))

allowed_users = {"admin", "editor", "viewer"}

if "admin" in allowed_users:
    print("Access granted")

# Why this matters:
    # in on a list → O(n)
    # in on a set → O(1)⚡