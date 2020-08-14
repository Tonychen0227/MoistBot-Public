import socket
import time
import sys
from StaticUtilities import *
import os
import binascii
from ScreenUtility import *
from Offsets import *


class StaticTradeClient:
    def __init__(self, ip, port, folder="ek8s"):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, int(port)))
        self.socket.settimeout(5)
        self.send_command('configure echoCommands 0')
        self.folder = folder

    def __del__(self):
        try:
            self.socket.shutdown(socket.SHUT_WR)
            self.socket.close()
        except OSError:
            pass

    # region Button Helpers
    def send_command(self, content):
        command = content + '\r\n'  # important for the parser on the switch side
        self.socket.sendall(command.encode())

    # Interprets sequence of strings in arraylist
    def interpret_string_list(self, arr):
        length = len(arr)
        i = 0
        while i < length:
            self.send_command(arr[i])
            i += 1
            time.sleep(0.60)

    def press_button(self, button):
        self.send_command("click " + button)
        time.sleep(1.5)
    # endregion

    # region Command Helpers
    def load_pokemon(self, path_to_ek8):
        print(f"loading {path_to_ek8}")
        mon_file = open(os.getcwd() + f"\\{self.folder}\\" + path_to_ek8, "rb")
        mon_data = mon_file.read(344)
        mon = str(binascii.hexlify(mon_data), "utf-8")
        self.send_command(f"poke {BoxStartOffset} 0x{mon}")  # inject it into box1slot1 for trade

    def clean_ram(self):
        print("cleaning ram")
        # Set critical parts of memory to 0
        self.send_command(f"poke {LanturnBotMatchOffset} 0x00000000")
        time.sleep(1)
        self.send_command(f"poke {LanturnBotMatchOffset} 0x00000000")
        time.sleep(1)

    def get_current_screen(self):
        self.send_command(f"peek {CurrentScreenOffset} 4")
        time.sleep(0.5)

        screen = ""

        proceed = False
        while not proceed:
            try:
                screen = self.socket.recv(9)
                screen = convert_to_bytes(screen)
                proceed = True
            except Exception as e:
                print(f"exception: {e}")
                self.send_command(f"peek {CurrentScreenOffset} 4")
                time.sleep(0.5)
        return screen

    # endregion
    def do_giveaway(self):
        list_dir = os.listdir(os.getcwd() + f"\\{self.folder}\\")

        for x in list_dir:
            self.trade(x)

    def trade(self, mon):
        self.load_pokemon(mon)
        can_trade = self.wait_and_process_offer()

        if can_trade:
            self.press_button("A")
            self.press_button("A")
            self.press_button("A")
            self.press_button("A")
            self.press_button("A")
            start_time = time.time()
            while True:
                screen = self.get_current_screen()
                if is_correct_screen(screen, ScreenType_BoxView):
                    pass
                elif is_correct_screen(screen, ScreenType_Warning) or start_time + 25 < time.time():
                    self.clean_ram()
                    print("trade is going")
                    time.sleep(10)
                    break
                else:
                    self.press_button("A")

            while True:
                screen = self.get_current_screen()
                if is_correct_screen(screen, ScreenType_BoxView):
                    print("done")
                    return
                elif is_correct_screen(screen, ScreenType_SoftBan) and start_time + 90 < time.time():
                    print("WTF softbanned")
                    return
                else:
                    self.press_button("B")

    def wait_and_process_offer(self):
        # Wait for a mon to pop
        while True:
            mem_check = 0

            self.send_command(f"peek {LanturnBotMatchOffset} 4")
            time.sleep(0.5)

            proceed = False
            while not proceed:
                try:
                    mem_check = self.socket.recv(689)
                    mem_check = int(convert_to_bytes(mem_check), 16)
                    proceed = True
                except:
                    self.send_command(f"peek {LanturnBotMatchOffset} 4")
                    time.sleep(0.5)

            if mem_check != 0:
                return True


client = StaticTradeClient(sys.argv[1], sys.argv[2], sys.argv[3])
client.do_giveaway()
