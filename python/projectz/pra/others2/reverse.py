def reverseInput(value : str):
    i = len(value)-1
    reverseValue = ''
    while(i >= 0):
        reverseValue += value[i]
        i -= 1;
    return reverseValue;