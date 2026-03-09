import time
import numpy as np

size = 10000000

print(f"Creating two lists and two NumPy arrays of size {size}...")
print("This may take a moment...")

list_one = list(range(size))
list_two = list(range(size))

nparray_one = np.array(list_one)
nparray_two = np.array(list_two)

start_time = time.time()
result_list = [x + y for x, y in zip(list_one, list_two)]
end_time = time.time()
print(f"Time taken for list addition: {end_time - start_time:.6f} seconds")

start_time = time.time()
result_array = nparray_one + nparray_two
end_time = time.time()
print(f"Time taken for NumPy array addition: {end_time - start_time:.6f} seconds")