class Employee:
    def __init__(self, name: str, base_salary: float):
        self.name = name
        self.base_salary = base_salary

    def monthly_pay(self) -> float:
        return self.base_salary

class ContractEmployee(Employee):
    def __init__(self, name: str, hourly_rate: float, hours: int):
        super().__init__(name, base_salary=0)
        self.hourly_rate = hourly_rate
        self.hours = hours

    def monthly_pay(self) -> float:
        return self.hourly_rate * self.hours

class PermanentEmployee(Employee):
    def __init__(self, name: str, base_salary: float, bonus: float):
        super().__init__(name, base_salary)
        self.bonus = bonus

    def monthly_pay(self) -> float:
        return self.base_salary + self.bonus


staff = [
    ContractEmployee("Asha", 1000, 40),
    PermanentEmployee("Manava", 120000, 15000),
]

for emp in staff:
    print(emp.name, emp.monthly_pay())
