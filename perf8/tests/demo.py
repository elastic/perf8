import time
import random

data = []

for i in range(4000):
    data.append(random.randint(1, 3722837687624) ** 4)
    data.append("r" * random.randint(10000, 2000000))
    if random.randint(1, 20) == 2:
        print(f"Busy adding data! ({i}/4000)")
        time.sleep(0.1)
