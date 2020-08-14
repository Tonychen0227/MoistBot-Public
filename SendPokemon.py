import socket
import sys
import os
import binascii
from Offsets import *

#Get the raw data
mon_file = open(os.getcwd() + "\\all_pk_files\\" + sys.argv[2] + ".ek8", "rb")
mon_data = mon_file.read(344)
mon = str(binascii.hexlify(mon_data), "utf-8")

socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_connection.connect((sys.argv[1], 6000))


def send_command(content):
    command = content + '\r\n'  # important for the parser on the switch side
    socket_connection.sendall(command.encode())


send_command(f"poke {BoxStartOffset} 0x{mon}")
socket_connection.shutdown(socket.SHUT_WR)
socket_connection.close()
