# coding=utf-8
from itertools import chain
import math


def list_squared(start, stop):
    result = []

    for num in range(start, stop):
        # chain
        # [i, num/i]目的是取对应的余数, int(math.sqrt(num)) + 1 是边界条件。
        # 当num/i == i 时成立，所以i最大值为sqrt(num)
        divisors = set(chain.from_iterable((
            [i, num / i] for i in range(1, int(math.sqrt(num)) + 1)
            if num % i == 0
        )))
        divisor_squares = [x * x for x in divisors]
        divisor_squares_sum = sum(divisor_squares)
        if math.sqrt(divisor_squares_sum).is_integer():
            result.append([num, divisor_squares_sum])

    return result


if __name__ == "__main__":
    print list_squared(1, 5)
