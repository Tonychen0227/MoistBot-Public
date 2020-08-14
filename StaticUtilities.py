from PK8 import PK8
from FirebaseService import FirebaseService

def convert_to_string(arr):
    size = len(arr)
    i = 0
    strings = list()
    accumulator = ""
    while i < size:
        if arr[i] == 0x0A:
            strings.append(accumulator)
            accumulator = ""
        if arr[i] != 0x0D or arr[i] != 0x0A:
            accumulator = accumulator + str(chr(arr[i]))
        i += 1

    return accumulator


def convert_to_int(bytedata, length):
    data = list()
    j = 0
    i = 0
    while j < length:
        if bytedata[j] == 0x0A:
            break
        digit = str(chr(bytedata[i])) + str(chr(bytedata[i + 1]))
        data.append(int(digit, 16))
        j += 1
        i += 2

    return data


def convert_to_bytes(arr):
    size = len(arr)
    i = 0
    accumulator = ""
    while i < size:
        if arr[i] == 0xA:
            break
        accumulator = accumulator + str(chr(arr[i]))
        i += 1

    return accumulator


# region CONSTANTS
trade_evo_pkdex_numbers = [
    525,  # Boldore
    366,  # Clamperl
    356,  # Dusclops
    125,  # Electabuzz
    349,  # Feebas
    75,   # Graveler
    533,  # Gurdurr
    93,   # Haunter
    64,   # Kadabra
    588,  # Karrablast
    67,   # Machoke
    126,  # Magmar
    95,   # Onix
    708,  # Phantump
    61,   # Poliwhirl
    137,  # Porygon
    233,  # Porygon-2
    710,  # Pumpkaboo
    112,  # Rhydon
    123,  # Scyther
    117,  # Seadra
    616,  # Shelmet
    79,   # Slowpoke
    682,  # Spiritzee
    684,  # Swirlix
]
# endregion


def verify_not_trade_evo(pk8: PK8):
    species = pk8.getSpecies()
    firebase = FirebaseService()
    firebase.update_offered_species(species)
    return species not in trade_evo_pkdex_numbers


def verify_ot_trainer(pk8: PK8, trainer_name):
    OT_name = pk8.getOTName().hex()

    if trainer_name != OT_name:
        return False

    return True
