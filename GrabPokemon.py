import os
import binascii
import sys
from PK8 import PK8

#Get the raw data
mon_file = open(os.getcwd() + "\\ek8s\\" + sys.argv[1] + ".ek8", "rb")
mon_data = mon_file.read(344)
mon = str(binascii.hexlify(mon_data), "utf-8")
ek8 = PK8(mon)


print(ek8.isShiny())