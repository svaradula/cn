from typing import NamedTuple

class User(NamedTuple):
    id: int
    name: str
    role: str

u = User(1, "Manava", "SE")
print(u.name, u.id)
