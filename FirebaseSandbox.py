from FirebaseService import *
import binascii
import os
from ClientStrategy import OfflineStrategy
from PK8 import PK8

service = FirebaseService()


def send_pokemon_to_firebase():
    db = service.firebase.database()
    pokemon_information = db.child("pokemon_buckets").child(os.getenv("pokemon_bucket")).child(os.getenv("pokemon_category"))

    mon_file = open(os.getcwd() + "\\all_pk_files\\" + os.getenv("pokemon_file") + ".ek8", "rb")
    mon_data = mon_file.read(344)
    mon = str(binascii.hexlify(mon_data), "utf-8")

    key = os.getenv("pokemon_key")
    IV = os.getenv("pokemon_iv")
    OT = os.getenv("pokemon_ot")
    country = os.getenv("pokemon_country")
    heldItem = os.getenv("pokemon_heldItem")
    nature = os.getenv("pokemon_nature")
    species = os.getenv("pokemon_species")
    ability = os.getenv("pokemon_ability")

    new_object = {
        key: {
            "IV": IV,
            "OT": OT,
            "country": country,
            "heldItem": heldItem,
            "nature": nature,
            "species": species,
            "rawData": mon,
            "isLive": True,
            "isShiny": os.getenv("pokemon_shiny") == "1",
            "ability": ability
        }
    }

    for x in ["country", "heldItem", "nature"]:
        if type(new_object[key][x]) == str:
            continue
        new_object[key][x] = new_object[key][x][0]

    pokemon_information.update(new_object)


def update_is_shiny():
    db = service.firebase.database()
    pokemon_information = db.child("pokemon_buckets").child("Item").get().pyres
    for pyre in pokemon_information:
        print(pyre.key())
        for key in pyre.val().keys():
            db.child("pokemon_buckets").child("Item").child(pyre.key()).child(key).update({"isShiny": False})


def batch_update_community():
    db = service.firebase.database()
    pokemon_information = db.child("pokemon_buckets").child("Community").child("SwShGmax")
    for x in pokemon_information.get().pyres:
        key = x.key()
        file_key = key[4:]
        mon_file = open(os.getcwd() + "\\ek8s\\" + file_key + ".ek8", "rb")
        mon_data = mon_file.read(344)
        mon = str(binascii.hexlify(mon_data), "utf-8")
        print(key, mon)
        db = service.firebase.database()
        db.child("pokemon_buckets").child("Community").child("SwShGmax").child(key).update({"rawData": mon})


def download_all():
    db = service.firebase.database()
    buckets = ["Community", "Item"]
    for bucket in buckets:
        categories = service.get_pokemon_categories(bucket)
        for category in categories:
            pokemon = service.get_pokemon_category(bucket, category)
            total_count = 0
            suffix = 0
            while total_count < 20:
                for mon in pokemon:
                    mon_data = service.get_pokemon_information(bucket, category, mon)
                    ek8_out = open(f"all_pk_files/{mon}{str(suffix)}.ek8", "wb")
                    raw_data = mon_data["rawData"]
                    raw_data = binascii.unhexlify(raw_data)
                    ek8_out.write(bytes(raw_data))
                suffix += 1
                total_count += len(pokemon)

send_pokemon_to_firebase()