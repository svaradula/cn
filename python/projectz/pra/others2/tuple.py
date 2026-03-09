# tuple — Ordered, immutable

# Database connection configuration
db_config = ("localhost", 5432, "admin", "password")

host, port, user, password = db_config

print(f"Connecting to {host}:{port} as {user}")
