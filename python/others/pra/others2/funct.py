def greet(name):
    return f"Hey, {name}!"

print(greet('Pu'))

def calculate_tax(amount, rate=0.18):
    return amount * rate

# print(calculate_tax(25000))

def analyze_text(text):
    return len(text), text.upper()

length, upperedText = ( analyze_text(greet('One Two')) )

# print(length, upperedText)

def stats(numbers):
    return min(numbers), max(numbers), sum(numbers)

min_val, max_val, total = stats([1, 2, 3])

print(min_val,max_val, total)