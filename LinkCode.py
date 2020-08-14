from random import randint
import time

banned_codes = [1111, 2222, 3333, 4444, 5555, 6666, 7777, 8888, 9999, 0000, 1234, 2345, 3456, 4567, 5678, 6789, 7890,
                1357, 2468, 3579, 4680, 4321, 5432, 6543, 7654, 8756, 9867, 987, 7531, 8642, 9753, 864, 1470, 8008,
                9162,
                111, 222, 333, 444, 555, 666, 777, 888, 999,
                6969, 420, 4200, 1337, 135, 246, 357, 468, 579, 680, 531, 642, 753, 864, 975, 123, 234, 345, 456, 567,
                678, 789, 890,
                321, 432, 543, 654, 765, 876, 987]


def random_link_code():
    flag = False
    random_code = str(randint(10000000, 100000000))
    while not flag:
        random_code = str(randint(10000000, 100000000))
        for banned in banned_codes:
            if str(banned) in str(random_code) or '0' in str(random_code):
                flag = False
                break
            flag = True

    return random_code
