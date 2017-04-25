def show_sequence(n):
    if not n:
        return '0=0'
    elif n < 0:
        return '%d<0' % n
    else:
        from_0_to_n = list(range(n + 1))
        return '%s = %d' % ('+'.join([str(num) for num in from_0_to_n]), sum(from_0_to_n))


def show_sequence_better(n):
    if n == 0:
        return "0=0"
    return "{} = {}".format("+".join(map(str, range(n + 1))), sum(range(n + 1))) if n > 0 else "{}<0".format(n)
