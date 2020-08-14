import socket
import time
import sys


class RemoteController:
    def __init__(self, ip, port):
        print("foo")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, int(port)))

    def __del__(self):
        self.socket.shutdown(socket.SHUT_WR)
        self.socket.close()

    def convert_to_string(self, arr):
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

    def convert_to_int(self, bytedata, length):
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

    def send_command(self, content):
        command = content + '\r\n'  # important for the parser on the switch side
        self.socket.sendall(command.encode())

    def press_button(self, button):
        self.send_command("click " + button)
        time.sleep(1)

    # New interpreter for new packet structure
    def convert_to_bytes(self, arr):
        size = len(arr)
        i = 0
        accumulator = ""
        while i < size:
            if arr[i] == 0xA:
                break
            accumulator = accumulator + str(chr(arr[i]))
            i += 1

        return accumulator

client = RemoteController(sys.argv[1], sys.argv[2])

for button in sys.argv[3].split(','):
    client.press_button(button)
