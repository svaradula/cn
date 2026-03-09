class Order:
    _next_id = 1

    def __init__(self, amount):
        self.id = Order._next_id
        self.amount = amount
        Order._next_id += 1

o1 = Order(100)
o2 = Order(2000);

print(Order._next_id);

print(o1.id, o2.id)