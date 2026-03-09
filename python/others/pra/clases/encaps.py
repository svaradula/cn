class Wallet:
    def __init__(self):
        self.__balance = 0  # name-mangled

    def add_money(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        self.__balance += amount

    def spend(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount > self.__balance:
            raise ValueError("Not enough funds.")
        self.__balance -= amount

    def get_balance(self) -> int:
        return self.__balance


w = Wallet()
w.add_money(200)
w.spend(50)
# print(w.__balance)  # This creates a new attribute, doesn't change the original __balance
print(w.get_balance())

# print(w.__balance)  # AttributeError (can't access directly)
