from reverse import reverseInput

def ifPalindorm(value):
    if(reverseInput(value) == value):
        return True
    return False

value = 'abccbae';
print(ifPalindorm(value))