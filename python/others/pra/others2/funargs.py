def sumthenumbers(*numbers):
    if 3 in numbers:
        return 0
    for n in numbers:
        print(n)
    print("-------")
    return sum(numbers)

# print(sumthenumbers(1,2,3))

def printdetails(**jsonfile):  #qwargs
    print(jsonfile)  # return dict
 
printdetails(name="test")