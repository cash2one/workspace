import math


def is_square(n):
    step = 1
    while n > 0:
        n -= step
        step += 2
    return 0 == n

if __name__ == "__main__":
    print is_square(9)
