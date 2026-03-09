sum = lambda a, b: a + b
print(sum(3, 5)) # 8

def incrementBy(x):
    return lambda a: a + x

incrementBy2 = incrementBy(2)
print(incrementBy2(5)) # 7


aPlugBWholeSquare = lambda a,b : (a**2) + (b**2) + (2*a*b)
print(aPlugBWholeSquare(3, 4)) # 49

# function to give a Square + b Square = c Square.
aSquarePlusbSquare = lambda a, b: (a**2) + (b**2)
print(aSquarePlusbSquare(3, 4)) # 25

 
