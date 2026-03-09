from logs.logger import log_account_activity

class BankAccount:
    def __init__(self, account_no: str, owner: str, balance: float = 0.0):
        self.account_no = account_no
        self.owner = owner
        self.balance = balance
        log_account_activity(self.owner + "_" + self.account_no, "Account Creation", "Success")

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            log_account_activity(self.owner + "_" + self.account_no, "Deposit", "Failed")
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        log_account_activity(self.owner + "_" + self.account_no, f"Deposited {amount}", "Success")

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            log_account_activity(self.owner + "_" + self.account_no, "Withdraw", "Failed")
            raise ValueError("Withdraw amount must be positive.")
        if amount > self.balance:
            log_account_activity(self.owner + "_" + self.account_no, "Withdraw", "Failed")
            raise ValueError("Insufficient funds.")

        log_account_activity(self.owner + "_" + self.account_no, f"Withdrew {amount}", "Success")
        self.balance -= amount

    def summary(self) -> str:
        return f"{self.owner} ({self.account_no}) -> Balance: {self.balance:.2f}"


acc1 = BankAccount("AC002", "Manava S", 1000)
acc1.deposit(100000)
acc1.withdraw(3000)
print(acc1.summary())
