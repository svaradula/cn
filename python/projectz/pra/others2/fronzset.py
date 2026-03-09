# frozenset — Unordered, immutable set

# Permissions for ADMIN role
ADMIN_PERMISSIONS = frozenset({
    "READ",
    "WRITE",
    "DELETE"
})

print("DELETE" in ADMIN_PERMISSIONS)  # True

print(ADMIN_PERMISSIONS)

# ADMIN_PERMISSIONS.add("EXECUTE")  # AttributeError

role_access_map = {
    frozenset({"READ"}): "Viewer",
    frozenset({"READ", "WRITE"}): "Editor",
    frozenset({"READ", "WRITE", "DELETE"}): "Admin"
}

print(role_access_map)
