initial_seed = 0x900A0319

rng_values = [0] * 20000

rng_values[0] = initial_seed

def mult32(a, b):
    c = a >> 16
    d = a % 0x10000
    e = b >> 16
    f = b % 0x10000
    g = (c*f + d*e) % 0x10000
    h = d*f
    i = g*0x10000+h
    return i

def rngAdvance(a):
    return mult32(a, 0x41C64E6D) + 0x6073

start_frame = 0

array_updated_to = 1

while array_updated_to <= start_frame:
    rng_values[array_updated_to] = rngAdvance(rng_values[array_updated_to - 1])
    array_updated_to += 1

with open("C:/Users/Tony's PC/Downloads/Yes.csv") as file:
    next(file)
    good = []
    for line in file:
        occid = int(line.split(',')[1]) + 4
        frame = int(line.split(',')[0])
        current = occid
        while array_updated_to <= current:
            rng_values[array_updated_to] = rngAdvance(rng_values[array_updated_to - 1])
            array_updated_to += 1
        modulo = int(hex(rng_values[occid])[:-4], 16) % 100
        if 95 <= modulo <= 99:
            print(frame)

print(int(hex(rng_values[502])[:-4], 16) % 100)