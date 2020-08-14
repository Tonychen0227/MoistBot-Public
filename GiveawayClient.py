import socket
import time
import sys
from NumpadInterpreter import *
from StaticUtilities import *
from FirebaseService import FirebaseService
from ScreenUtility import *
from ClientStrategy import DuduStrategy, DittoStrategy
import uuid
import traceback
from Offsets import *


class GiveawayClient:
    def __init__(self, agent_name, ip, port, agent_type="ditto"):
        self.firebase_service = FirebaseService()
        self.client = self.firebase_service.add_client(agent_name, ip, port, agent_type)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, int(port)))
        self.socket.settimeout(5)
        self.send_command('configure echoCommands 0')
        self.cached_mon_name = ""
        self.cached_mon_data = ""
        self.strategy = None
        self.giveaway = None

    def __del__(self):
        try:
            self.socket.shutdown(socket.SHUT_WR)
            self.socket.close()
        except Exception as exception:
            print(f"exception: {exception}", flush=True)
            print(traceback.format_exc(), flush=True)
            pass
        time.sleep(10)

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

    def input_link_code_and_begin(self, link_code):
        self.log(f"inputting link code {link_code}")
        time.sleep(1)
        self.press_button("Y")
        time.sleep(0.5)
        self.press_button("A")
        self.press_button("DDOWN")
        self.press_button("A")
        self.press_button("A")
        time.sleep(2)
        datalist, code = getButtons(link_code)
        self.interpret_string_list(datalist)
        self.press_button("PLUS")
        self.press_button("A")
        self.press_button("A")
        self.press_button("A")
        self.clean_ram()
        self.press_button("A")

    def early_exit_trade(self):
        self.log("exiting trade early")
        self.press_button("B")
        self.press_button("A")
        time.sleep(1.0)
        self.press_button("B")
        self.press_button("B")
        self.press_button("A")

    def exit_trade(self):
        self.log("exiting trade")
        self.press_button("B")
        time.sleep(5.0)
        self.press_button("B")
        self.press_button("B")
        self.press_button("B")
        self.press_button("A")
        self.press_button("B")
        self.press_button("B")
        self.press_button("A")
        time.sleep(1.0)

    def exit_menu_trade(self):
        self.log("exiting menu trade")
        self.press_button("Y")
        time.sleep(7)

        screen = self.get_current_screen()

        if not is_correct_screen(screen, ScreenType_YComms):
            if is_correct_screen(screen, ScreenType_BoxView):
                return False
            else:
                self.restart_game()
                return True

        self.press_button("A")
        self.press_button("A")
        self.press_button("A")
        self.press_button("A")
        self.press_button("A")
        self.press_button("B")
        self.press_button("B")
        time.sleep(1.0)
        return True

    def restart_game(self):
        self.log("restarting the game")
        self.press_button("HOME")
        time.sleep(1)
        self.press_button("X")
        self.press_button("A")
        time.sleep(5)
        self.press_button("A")
        time.sleep(1)
        self.press_button("A")
        for x in range(0, 15):
            self.press_button("A")
            time.sleep(1)
        self.connect()

    def unban(self):
        self.log("unbanning")
        self.send_command(f"poke {SoftBanUnixTimespanOffset} 0x00000000")

    def connect(self):
        self.press_button("Y")
        time.sleep(2)
        self.log("connecting to internet")
        self.press_button("PLUS")
        self.press_button("A")
        self.press_button("A")
        for x in range(0, 10):
            self.press_button("B")
            time.sleep(1)
        while not self.get_is_overworld():
            self.press_button("B")

# endregion

# region Command Helpers
    def log(self, log_string):
        self.firebase_service.add_log(self.client["name"], log_string)
        
    def load_pokemon(self):
        is_dudu = isinstance(self.strategy, DuduStrategy)
        if is_dudu:
            self.log(f"loading dudu")
        else:
            self.log(f"loading {self.cached_mon_name}")
        self.send_command(f"poke {BoxStartOffset} 0x{self.cached_mon_data}")  # inject it into box1slot1 for trade

    def clean_ram(self):
        self.log("cleaning ram")
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
                self.log(f"exception: {e}")
                self.log(traceback.format_exc())
                self.send_command(f"peek {CurrentScreenOffset} 4")
                time.sleep(0.5)
        return screen

    def get_is_overworld(self):
        self.send_command(f"peek {OverworldOffset} 4")
        time.sleep(0.5)

        screen = ""

        proceed = False
        while not proceed:
            try:
                screen = self.socket.recv(9)
                screen = convert_to_bytes(screen)
                proceed = True
            except Exception as e:
                self.log(f"exception: {e}")
                self.log(traceback.format_exc())
                self.send_command(f"peek {OverworldOffset} 4")
                time.sleep(0.5)
        return screen == "01010001"

    def get_connected(self):
        self.send_command(f"peek {IsConnectedOffset} 4")

        status = self.socket.recv(9)
        status = convert_to_bytes(status)
        return status != "00000000"

    def is_searching(self):
        self.send_command(f"peek {LinkTradeSearchingOffset} 4")

        status = self.socket.recv(9)
        status = convert_to_bytes(status)
        return status[0:1] == "01"

# endregion
    def do_giveaway(self):
        self.setup_teardown()
        client_status = self.firebase_service.get_client(self.client["name"])
        if not client_status["isRunning"]:
            self.log("client is not running, sleeping")
            self.press_button("A")
            time.sleep(30)
            return

        if client_status["type"] == "ditto":
            self.strategy = DittoStrategy(self)
        else:
            self.log("no valid type found, sleeping")
            self.press_button("A")
            time.sleep(30)
            return

        giveaway = self.strategy.load_giveaway()

        self.giveaway = giveaway

        if giveaway is None:
            self.log("no current giveaway found, sleeping")
            self.press_button("A")
            time.sleep(30)
            return

        if giveaway["type"] == "dudu":
            self.strategy = DuduStrategy(self)

        if self.cached_mon_name != giveaway["species"]:
            self.cached_mon_name = giveaway["species"]
            self.cached_mon_data = giveaway["speciesData"]

        self.load_pokemon()
        self.search_and_trade(giveaway["linkCode"])

    def setup_teardown(self):
        self.load_pokemon()
        connected = self.get_connected()

        if not connected:
            self.connect()

        self.unban()

        screen = self.get_current_screen()

        if self.is_searching():
            self.exit_menu_trade()

        if self.get_is_overworld():
            if not self.is_searching():
                return
            else:
                self.exit_menu_trade()
                return

        self.restart_game()

    def await_match(self):
        start = time.time()
        # Wait for a trade to pop
        while True:
            screen = self.get_current_screen()

            end = time.time()

            if is_correct_screen(screen, ScreenType_BoxView):
                self.log("found a match!")
                break

            if (end - start) >= 120:
                self.log("timed out, stale code")
                if not self.exit_menu_trade():
                    break
                self.firebase_service.update_total_stale(self.giveaway["log_key"], self.giveaway["log_type"])
                return False
        return True

    def wait_for_overworld(self):
        start = time.time()

        while True:
            end = time.time()
            if (end - start) >= 30:
                self.restart_game()
                return

            if self.get_is_overworld():
                return

    def monitor_and_do_trade(self):
        self.log("beginning to monitor trade")
        can_trade = self.await_match()

        if can_trade:
            can_trade = self.wait_and_process_offer()
        else:
            return

        if can_trade:
            self.press_button("A")
            time.sleep(2)
            self.press_button("A")
            time.sleep(5)
            self.press_button("A")
            takeback_protection = 0
            start_time = time.time()
            while True:
                screen = self.get_current_screen()
                if is_correct_screen(screen, ScreenType_BoxView):
                    if takeback_protection > 10:
                        self.log("takeback detected")
                        self.firebase_service.update_total_ghosted(self.giveaway["log_key"], self.giveaway["log_type"])
                        self.early_exit_trade()
                        self.wait_for_overworld()
                        return
                    else:
                        takeback_protection += 1
                elif is_correct_screen(screen, ScreenType_Warning) or start_time + 25 < time.time():
                    start_time = time.time()
                    self.log("trade is going")
                    time.sleep(10)
                    break
                else:
                    takeback_protection = 0
                    self.press_button("A")

            while True:
                screen = self.get_current_screen()
                if is_correct_screen(screen, ScreenType_BoxView) or self.get_is_overworld():
                    self.log("trade is confirmed done")
                    self.firebase_service.update_total_sent(self.giveaway["log_key"], self.giveaway["log_type"])
                    break
                elif start_time + 60 < time.time():
                    self.restart_game()
                    return
                else:
                    self.press_button("B")

            self.exit_trade()
            self.wait_for_overworld()
            return

        self.early_exit_trade()
        self.wait_for_overworld()

    def wait_and_process_offer(self):
        start = time.time()
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
                except Exception as exception:
                    self.log(f"exception: {exception}")
                    self.log(traceback.format_exc())
                    self.send_command(f"peek {LanturnBotMatchOffset} 4")
                    time.sleep(0.5)

            end = time.time()
            if mem_check != 0:
                try:
                    guid = uuid.uuid4()
                    self.log(f"loading pokemon with ID {guid}")
                    self.send_command(f"peek {LinkTradePartnerPokemonOffset} 328")
                    time.sleep(0.5)
                    ek8 = self.socket.recv(689)
                    data = convert_to_int(ek8, 0x148)
                    decryptor = PK8(data)
                    decryptor.decrypt()
                    pk8 = decryptor.getData()
                    pk8_out = open(f"logged_pk_files/{guid}.pk8", "wb")
                    pk8_out.write(bytes(pk8))
                    pk8_out.close()
                except Exception as exception:
                    self.log(f"error loading pokemon with exception {exception}")
                    self.log(traceback.format_exc())
                    return False

                self.send_command(f"peek {LinkTradePartnerNameOffset} 24")
                partner_name = self.socket.recv(49)[:-2].decode('utf-8').lower() + '0'

                if self.strategy.process_details(decryptor, partner_name, str(guid)):
                    requested_mon = self.strategy.is_specific_request(decryptor)
                    if requested_mon is not False:
                        self.send_command(f"poke {BoxStartOffset} 0x{requested_mon}")
                    return True
                else:
                    return False

            if (end - start) >= 30:
                return False

    def search_and_trade(self, link_code):
        self.input_link_code_and_begin(link_code)
        self.monitor_and_do_trade()


def generate_client():
    if len(sys.argv) != 4 and len(sys.argv) != 5:
        quit()
    if len(sys.argv) == 5:
        return GiveawayClient(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        return GiveawayClient(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    client = generate_client()
    while True:
        try:
            client.do_giveaway()
        except TimeoutError as e:
            client.log(f"exception: {e}")
            client.log(traceback.format_exc())
            client = generate_client()
            continue
        except OSError as e:
            client.log(f"exception: {e}")
            client.log(traceback.format_exc())
            client = generate_client()
            continue
