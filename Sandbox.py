import socket
import sys
from StaticUtilities import convert_to_int
from PK8 import PK8
from time import sleep
from math import pow
from Offsets import *
import os

socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_connection.connect((sys.argv[1], int(sys.argv[2])))
socket_connection.settimeout(5)

def send_command(content):
    command = content + '\r\n'  # important for the parser on the switch side
    socket_connection.sendall(command.encode())
send_command(f"peek {BoxStartOffset} 328")
ek8 = socket_connection.recv(689)
data = convert_to_int(ek8, 0x148)
decryptor = PK8(data)
decryptor.decrypt()
check = decryptor.getSpecies()
print(decryptor.getNickname().decode("utf-8"))
pk8 = decryptor.getData()
pk8_out = open(f"TestTestTest.pk8", "wb")
pk8_out.write(bytes(pk8))
pk8_out.close()

socket_connection.shutdown(socket.SHUT_WR)
socket_connection.close()
