class Car:
    def __init__(self, brand, year):
        self.brand = brand
        self.year = year

# c1 = Car("Toyota", 2022)
# c2 = Car("Tesla", 2024)


class User:
    company = "OpenAI"
    userCounter = 0;

    def __init__(self, name):
        self.name = name
        User.userCounter += 1

    def greet(self):
        print(f"Hi, I am {self.name}")
    
    


u = User('Pu') 
u.greet() # internally it is User.greet(u)

u1 = User("A")
u2 = User("B")

print(u1.company)
print( User.userCounter )


class MathUtil:
    @staticmethod
    def is_even(n):
        return n % 2 == 0

print( MathUtil.is_even(100))






