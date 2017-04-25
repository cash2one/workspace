# def sort_array(source_array):
#     for idx in range(len(source_array)):
#         for idy in range(len(source_array) - idx - 1):
#             if source_array[idy] > source_array[idy + 1]:
#                 source_array[idy], source_array[idy + 1] = source_array[idy + 1], source_array[idy]
#     return source_array


def sort_array(source_array):
    odd_array = [list(odd) for odd in enumerate(source_array) if odd[1] % 2 == 1]
    for idx in range(len(odd_array)):
        for idy in range(len(odd_array) - idx - 1):
            if odd_array[idy][1] > odd_array[idy + 1][1]:
                odd_array[idy][1], odd_array[idy + 1][1] = odd_array[idy + 1][1], odd_array[idy][1]
    for k, v in odd_array:
        source_array[k] = v
    return source_array


def sort_array_better(arr):
    odds = sorted((x for x in arr if x % 2 != 0), reverse=True)
    return [x if x % 2 == 0 else odds.pop() for x in arr]


def sort_array_better2(source_array):
    odds = iter(sorted(v for v in source_array if v % 2))
    return [next(odds) if i % 2 else i for i in source_array]


if __name__ == "__main__":
    print sort_array([5, 3, 2, 8, 1, 4])
