#dict Key–value mapping

# User profile data
user_profile = {
    "id": 101,
    "name": "Manava",
    "email": "manava@example.com",
    "revoked": [],
    "roles": ["ADMIN", "EDITOR"],
    "is_active": True
}

# Update email
user_profile["email"] = "new_email@example.com"
user_profile["revoked"] = user_profile["roles"]
user_profile["roles"] = ["READ"];


# Add last login time
user_profile["last_login"] = "2026-02-05 10:30"

print(user_profile)

if "ADMIN" in user_profile["roles"]:
    print("Admin access granted")
else:
    print("No Admin access.")
 