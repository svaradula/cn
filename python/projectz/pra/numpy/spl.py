import numpy as np

def zeroArr(r,c):
    return np.zeros((r, c))

def oneArr(r,c):
    return np.ones((r, c))

def eyeArr(r,c):
    return np.eye(r, c)

def fullArr(r,c):
    return np.full((r, c), 7)

def arrRange(start, stop, step):
    return np.arange(start, stop, step)

def linspaceArr(start, stop, num):
    return np.linspace(start, stop, num)

print(zeroArr(1,2))
print(oneArr(1,2))
print(eyeArr(5,5))
print(fullArr(5,5))
print(arrRange(0, 30, 2))
print(linspaceArr(1, 10, 10))

arr = np.arange(1, 17)
print(arr)
arr = arr.reshape(4,4)
print(arr)

print(np.random.rand(2,2))
print(np.random.randint(1, 100, (2,2)))
