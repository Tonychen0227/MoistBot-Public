from abc import ABC, abstractmethod
from StaticUtilities import verify_not_trade_evo, verify_ot_trainer, convert_to_int, convert_to_bytes, convert_to_string
import time
from PK8 import PK8
from raid_solver import search
from FirebaseService import FirebaseService
import random
import os
import binascii
import difflib


class ClientStrategy(ABC):
    def __init__(self, client):
        self.client = client
        self.firebase_service = FirebaseService()
        self.cached_pokemon = {}
        self.cached_list_bucket = ""
        self.cached_list_category = ""

    @abstractmethod
    def load_giveaway(self):
        pass

    @abstractmethod
    def process_details(self, decryptor: PK8, partner_name: str, logged_file: str):
        pass

    @abstractmethod
    def is_specific_request(self, decryptor: PK8):
        pass


class DuduStrategy(ClientStrategy):
    def find_and_publish_seed(self, decryptor: PK8, partner_name, logged_file):
        ec = decryptor.getEncryptionConstant()
        pid = decryptor.getPID()
        ivs = list(decryptor.getIVs())
        species = decryptor.getSpecies()
        ivs[3], ivs[4] = ivs[4], ivs[3]
        ivs[4], ivs[5] = ivs[5], ivs[4]

        seed = search(ec, pid, ivs)

        if not seed:
            seed = (f"No seed available :( your ec (as int): {ec}, your pid (as int): {pid}, your ivs: {ivs}"
                    f"You will need to convert: https://www.rapidtables.com/convert/number/decimal-to-hex.html\n")

        self.firebase_service.publish_seed(seed, species, partner_name, logged_file)

    def load_giveaway(self):
        self.firebase_service.add_log(self.client.client["name"], "something went wrong!")
        time.sleep(100000)

    def process_details(self, decryptor: PK8, partner_name: str, logged_file: str):
        partner_name_decoded = partner_name
        try:
            partner_name_decoded = "".join(bytearray.fromhex(partner_name).decode().split("\u0000"))
        except UnicodeDecodeError:
            pass
        self.client.log(f"seed checking for {partner_name_decoded}")

        self.find_and_publish_seed(decryptor, partner_name_decoded, logged_file)

    def is_specific_request(self, decryptor: PK8):
        return False


class DittoStrategy(ClientStrategy):
    def load_giveaway(self):
        dudu_giveaway = self.firebase_service.dudu_dequeue_if_possible(self.client.client["name"])
        if dudu_giveaway is not None:
            parseable_giveaway = {
                "linkCode": int(dudu_giveaway["linkCode"]),
                "species": "Ditto6IVBeastAdamant",
                "speciesData": self.firebase_service.get_pokemon_information("Ditto", "Ditto6IVBeastAdamant",
                                                                             "Ditto6IVBeastAdamant")["rawData"],
                "type": "dudu",
                "log_key": "dudu",
                "log_type": "dudu"
            }
            return parseable_giveaway

        current_giveaway = self.firebase_service.get_current_giveaway()[1]
        if current_giveaway["isOver"]:
            return

        if self.cached_list_bucket == current_giveaway["bucket"] and self.cached_list_category == current_giveaway["category"]:
            pass
        else:
            self.cached_pokemon = {}
            self.cached_list_bucket = current_giveaway["bucket"]
            self.cached_list_category = current_giveaway["category"]
            category = self.firebase_service.get_pokemon_category(current_giveaway["bucket"],
                                                                 current_giveaway["category"])
            for mon in category:
                data = self.firebase_service.get_pokemon_information(current_giveaway["bucket"], current_giveaway["category"], mon)
                self.cached_pokemon.update({mon: data["rawData"]})

        mon = random.choice(list(self.cached_pokemon.keys()))

        parseable_giveaway = {
            "linkCode": int(current_giveaway["linkCode"]),
            "species": mon,
            "speciesData": self.cached_pokemon[mon],
            "type": "ditto",
            "log_key": current_giveaway["epochTimestamp"],
            "log_type": current_giveaway["species"]
        }

        self.client.log(f"giving away {mon} at {parseable_giveaway['linkCode']}")

        return parseable_giveaway

    def verify_no_double_dip(self, pk8: PK8, giveaway_key, giveaway):
        tid = pk8.getTID()
        sid = pk8.getSID()
        tsv = pk8.getTSV()
        ot_name = pk8.getOTName().hex()

        if "dips" not in giveaway or giveaway["dips"] is None:
            self.firebase_service.add_dip(giveaway_key, ot_name, tid, sid, tsv)
            return True

        current_dips = giveaway["dips"]

        for dip in list(current_dips):
            if dip["SID"] == sid and dip["TID"] == tid and dip["TSV"] == tsv and dip["name"] == ot_name:
                self.client.log(f"double dipper: name: {ot_name}, TID/SID/TSV: {tid}/{sid}/{tsv}")
                return False

        self.firebase_service.add_dip(giveaway_key, ot_name, tid, sid, tsv)
        return True

    def process_details(self, decryptor: PK8, partner_name: str, logged_file: str):
        partner_name_decoded = partner_name
        try:
            partner_name_decoded = "".join(bytearray.fromhex(partner_name).decode().split("\u0000"))
        except UnicodeDecodeError:
            pass

        current_giveaway = self.firebase_service.get_current_giveaway()
        current_giveaway_key = current_giveaway[0]
        current_giveaway = current_giveaway[1]

        self.client.log(f"trading with with {partner_name_decoded}")
        self.firebase_service.update_user_statistics(partner_name_decoded)

        if not verify_not_trade_evo(decryptor):
            self.client.log("trade evo offered")
            self.firebase_service.update_total_did_not_read(self.client.giveaway["log_key"],
                                                            self.client.giveaway["log_type"])
            return False

        if not current_giveaway["canDoubleDip"] and not verify_ot_trainer(decryptor, partner_name):
            self.client.log(f"not caught by owner offered: {decryptor.getOTName().hex()} vs {partner_name}")
            self.firebase_service.update_total_did_not_read(self.client.giveaway["log_key"],
                                                            self.client.giveaway["log_type"])
            return False

        if not current_giveaway["canDoubleDip"] and not self.verify_no_double_dip(decryptor,
                                                                                  current_giveaway_key,
                                                                                  current_giveaway):
            self.client.log("double dip or invalid pokemon")
            self.firebase_service.update_total_did_not_read(self.client.giveaway["log_key"],
                                                            self.client.giveaway["log_type"])
            return False

        self.client.log("proceeding with trade")
        return True

    def is_specific_request(self, decryptor: PK8):
        try:
            nickname = decryptor.getNickname().decode("utf-8")

            self.client.log(f"nickname: {nickname.lower()}")

            nickname_lower = nickname.lower().strip().replace('\n', '')

            target = ""

            deconstructed_nickname = ""
            counter = 0
            for char in nickname_lower:
                if char.isalpha() or char.isdigit():
                    deconstructed_nickname = deconstructed_nickname + char
                    counter = 0
                else:
                    counter += 1

                if counter == 2:
                    break

            for key in self.cached_pokemon.keys():
                key_lower = key.lower().strip()

                if key_lower.find(deconstructed_nickname) != -1:
                    if target == "":
                        target = key
                    else:
                        return False

            self.client.log(f"curated nickname: {deconstructed_nickname}")

            if target == "":
                return False
            else:
                self.client.log(f"request found for {target}")
                return self.cached_pokemon[target]
        except:
            return False

class OfflineStrategy(ClientStrategy):
    def load_giveaway(self):
        species = os.listdir(os.getcwd() + '/all_pk_files')
        species = random.choice(species)
        mon_file = open(os.getcwd() + '/all_pk_files/' + species, "rb")
        mon_data = mon_file.read(344)
        mon = str(binascii.hexlify(mon_data), "utf-8")

        parseable_giveaway = {
            "linkCode": 34529886,
            "species": species,
            "speciesData": mon,
            "type": "ditto",
            "log_key": 0,
            "log_type": species
        }

        self.client.log(f"giving away {species} at {parseable_giveaway['linkCode']}")

        return parseable_giveaway

    def verify_no_double_dip(self, pk8: PK8, giveaway_key, giveaway):
        return True

    def process_details(self, decryptor: PK8, partner_name: str, logged_file: str):
        partner_name_decoded = partner_name
        try:
            partner_name_decoded = "".join(bytearray.fromhex(partner_name).decode().split("\u0000"))
        except UnicodeDecodeError:
            pass

        self.client.log(f"trading with with {partner_name_decoded}")

        if not verify_not_trade_evo(decryptor):
            self.client.log("trade evo offered")
            return False

        self.client.log("proceeding with trade")
        return True
