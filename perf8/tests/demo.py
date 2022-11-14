"""
Demo script to test perf8
"""
import random

data = []
RANGE = 100


def get_random(min, max):
    return random.randint(min, max)


def do_math(x, y):
    x * y
    y**x


def main():
    for i in range(RANGE):
        data.append(get_random(1, 3722837687624) ** 4)
        data.append("r" * get_random(10000, 2000000))
        if get_random(1, 20) == 2:
            print(f"Busy adding data! ({i}/{RANGE})")
            do_math(i, RANGE)


if __name__ == "__main__":
    main()
