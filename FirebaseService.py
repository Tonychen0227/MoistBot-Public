import pyrebase
import os
from datetime import datetime, timedelta, date
from urllib.parse import quote
from LinkCode import random_link_code
from time import sleep
import traceback
from StrawpollService import StrawpollService


def noquote(s):
    return s


pyrebase.pyrebase.quote = noquote

config = {
  "apiKey": os.environ["FIREBASE_API_KEY"],
  "authDomain": os.environ["FIREBASE_DOMAIN"],
  "storageBucket": os.environ["FIREBASE_STORAGE_BUCKET"],
  "databaseURL": os.environ["FIREBASE_DATABASE"]
}

class FirebaseService:
    def __init__(self):
        self.firebase = pyrebase.initialize_app(config)
        self.strawpoll_service = StrawpollService()

    def get_current_giveaway(self):
        db = self.firebase.database()
        giveaways = db.child("giveaways").order_by_child("epochTimestamp").limit_to_last(1).get().val()
        latest_giveaway = giveaways.popitem()
        return latest_giveaway

    def create_giveaway(self, total_duration_mins, theme_name, category, species):
        db = self.firebase.database()

        try:
            themes = db.child("themes").get().val()
            bucket = None
            select_next = False
            next_theme = themes[0]
            for theme in themes:
                if theme["name"] == theme_name:
                    bucket = theme["bucket"]
                    select_next = True
                elif select_next:
                    next_theme = theme
                    select_next = False

            db.child("pokemon_buckets").child(bucket).child(category).child(species).get()
        except Exception as e:
            print(f"exception, {e}", flush=True)
            print(traceback.format_exc(), flush=True)
            return False

        pokemon_categories = self.get_pokemon_categories(next_theme["bucket"])
        link_code = random_link_code()
        new_strawpoll = self.strawpoll_service.make_poll("What category of Pokemon to GA next?",
                                                         pokemon_categories)

        timestamp = int(datetime.timestamp(datetime.utcnow()))
        data = {
            "epochTimestamp": timestamp,
            "timestampString": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            "linkCode": link_code,
            "totalDurationMins": total_duration_mins,
            "theme": theme_name,
            "nextTheme": next_theme,
            "nextCategory": None,
            "nextSpecies": None,
            "bucket": bucket,
            "category": category,
            "species": species,
            "strawpoll": new_strawpoll,
            "isOver": False,
            "votingOnCategory": True,
            "canDoubleDip": True
        }

        db = self.firebase.database()
        giveaways = db.child("giveaways")
        all_giveaways = giveaways.order_by_child("epochTimestamp").get().pyres
        db.child("giveaways").child(all_giveaways[-1].key()).update({"isOver": True})
        db.child("giveaways").push(data)
        if len(all_giveaways) >= 10:
            db.child("giveaways").child(all_giveaways[0].key()).remove()
        return data

    def stop_current_giveaway(self):
        db = self.firebase.database()
        giveaways = db.child("giveaways")
        latest_giveaway = giveaways.order_by_child("epochTimestamp").limit_to_last(1).get().val()
        db.child("giveaways").child(latest_giveaway.popitem()[0]).update({"isOver": True})

    def update_next_giveaway_category(self, category):
        db = self.firebase.database()
        giveaways = db.child("giveaways")
        latest_giveaway = giveaways.order_by_child("epochTimestamp").limit_to_last(1).get().val()
        db.child("giveaways").child(latest_giveaway.popitem()[0]).update({"nextCategory": category,
                                                                          "votingOnCategory": False})

    def update_current_giveaway_strawpoll(self, new_strawpoll):
        db = self.firebase.database()
        giveaways = db.child("giveaways")
        latest_giveaway = giveaways.order_by_child("epochTimestamp").limit_to_last(1).get().val()
        db.child("giveaways").child(latest_giveaway.popitem()[0]).update({"strawpoll": new_strawpoll,
                                                                          "votingOnCategory": False})

    def get_current_giveaway_clients(self, client_type="ditto"):
        clients = self.firebase.database().child("clients").get()

        timestamp = int(datetime.timestamp(datetime.utcnow()))

        clients_ret = []
        for client in clients.pyres:
            if client.val()["type"] != client_type:
                continue

            threshold = timestamp - timedelta(seconds=120).seconds
            if "lastCommunication" in client.val().keys() and client.val()["lastCommunication"] > threshold:
                    clients_ret.append(client.key())

        return clients_ret

    def add_client(self, agent_name, ip_address, port, client_type="ditto"):
        db = self.firebase.database()
        clients = self.firebase.database().child("clients").get()

        agent_name_modified = agent_name
        counter = 2
        collision = True
        while collision:
            collision = False
            for client in clients.pyres:
                if client.key() == agent_name_modified:
                    if client.val()["ipAddress"] == ip_address and client.val()["port"] == port:
                        return client.val()
                    collision = True
                    break
            if collision:
                agent_name_modified = f"{agent_name}v{counter}"
                counter += 1

        new_client = {
            "name": agent_name_modified,
            "type": client_type,
            "ipAddress": ip_address,
            "port": port,
            "isRunning": True
        }

        db.child("clients").update({agent_name_modified: new_client})

        return new_client

    def get_client(self, agent_name):
        client = self.firebase.database().child("clients").child(agent_name).get()
        return client.val()

    def add_dip(self, giveaway_key, ot_name, tid, sid, tsv):
        db = self.firebase.database()
        latest_giveaway = db.child("giveaways").order_by_child("epochTimestamp").limit_to_last(1).get().pyres[0]
        if latest_giveaway.key() != giveaway_key or latest_giveaway.val()["canDoubleDip"]:
            return
        new_dip = {
            "name": ot_name,
            "TID": tid,
            "SID": sid,
            "TSV": tsv
        }
        if "dips" not in latest_giveaway.val() or latest_giveaway.val()["dips"] is None:
            current_dips = []
        else:
            current_dips = latest_giveaway.val()["dips"]
        current_dips.append(new_dip)
        db.child("giveaways").child(latest_giveaway.key()).update({"dips": current_dips})

    def add_log(self, agent_name, log):
        db = self.firebase.database()
        timestamp_epoch_s = int(datetime.timestamp(datetime.utcnow()))

        new_log = {
            "timestamp": timestamp_epoch_s,
            "timestampString": datetime.fromtimestamp(timestamp_epoch_s).strftime('%Y-%m-%d %H:%M:%S'),
            "log": log
        }

        print(f"log at {new_log['timestampString']}: {new_log['log']}", flush=True)

        db.child("clients").child(agent_name).update({"lastCommunication": new_log["timestamp"]})

    def dudu_enqueue(self, user_mention, is_chatot):
        db = self.firebase.database()
        current_queue = db.child("dudu_queue").get().val()

        if current_queue is None:
            current_queue = []

        for queued in current_queue:
            if queued['name'] == user_mention:
                return

        if not is_chatot:
            if not self.update_dudu_statistics(user_mention):
                return False

        new_item = {
            "name": user_mention,
            "timestamp": int(datetime.timestamp(datetime.utcnow())),
            "taken": "False",
            "linkCode": random_link_code(),
            "visited": False
        }

        current_queue.append(new_item)

        db.update({"dudu_queue": current_queue})

        return new_item

    def dudu_get_queue(self):
        db = self.firebase.database()
        current_queue = db.child("dudu_queue").get().val()
        if current_queue is None:
            return []
        return current_queue

    def dudu_get_place_in_queue(self, name):
        db = self.firebase.database()
        current = db.child("dudu_queue").get().val()
        if current is None:
            return -1
        index = 1
        for queued in current:
            if queued['name'] == name:
                 return index
            index += 1
        return -1

    def dudu_dequeue_if_possible(self, agent_name):
        db = self.firebase.database()
        current_queue = db.child("dudu_queue").get().val()
        if current_queue is None:
            return None
        current_queue = sorted(current_queue, key=lambda i: i['timestamp'])
        index = 0
        for queued in current_queue:
            if queued["taken"] == "False" and not queued["visited"]:
                queued["taken"] = agent_name
                queued["visited"] = False
                current_queue[index] = queued
                db.update({"dudu_queue": current_queue})
                break
        sleep(3)
        # in case race condition
        current_queue = db.child("dudu_queue").get().val()
        if current_queue is None:
            return None
        for queued in current_queue:
            if queued["taken"] == agent_name:
                return queued
        return None

    def dudu_remove_from_queue(self, name):
        db = self.firebase.database()
        current_queue = db.child("dudu_queue").get().val()
        index = 0
        new_queue = current_queue
        for queued in current_queue:
            if queued["name"] == name:
                new_queue.pop(index)
                break
            index += 1
        return db.update({"dudu_queue": new_queue})

    def dudu_set_visited(self, name):
        db = self.firebase.database()
        current_queue = db.child("dudu_queue").get().val()
        index = 0
        new_queue = current_queue
        for queued in current_queue:
            if queued["name"] == name:
                queued["visited"] = True
                new_queue[index] = queued
                break
            index += 1
        return db.update({"dudu_queue": new_queue})

    def get_pokemon_information(self, bucket, category, species):
        db = self.firebase.database()
        pokemon_information = db.child("pokemon_buckets").child(bucket).child(category).child(species).get()
        if len(pokemon_information.pyres) == 0:
            return False
        current_pokemon = pokemon_information.val()
        return dict(current_pokemon)

    def get_pokemon_category(self, bucket, category):
        db = self.firebase.database()
        pokemon_category = db.child("pokemon_buckets").child(bucket).child(category).get()
        if len(pokemon_category.pyres) == 0:
            return False
        pokemon_category = pokemon_category.val()
        return_keys = []
        for key in pokemon_category.keys():
            if pokemon_category[key]["isLive"]:
                return_keys.append(key)
        return return_keys

    def get_pokemon_categories(self, bucket):
        db = self.firebase.database()
        category_information = db.child("pokemon_buckets").child(bucket).get()
        if len(category_information.pyres) == 0:
            return False
        categories = []
        for category in category_information.pyres:
            for mon in category.val():
                mon_information = self.get_pokemon_information(bucket, category.key(), mon)
                if mon_information["isLive"]:
                    categories.append(category.key())
                    break

        return categories

    def get_last_ping_timestamp(self):
        db = self.firebase.database()
        last_ping_timestamp = db.child("last_ping_timestamp").get().val()
        return last_ping_timestamp

    def update_last_ping_timestamp(self):
        db = self.firebase.database()
        db.update({
            "last_ping_timestamp":
                int(datetime.timestamp(datetime.utcnow()))
        })

    def update_user_statistics(self, name):
        name = quote(name)
        today = str(date.today())
        db = self.firebase.database()
        statistics = db.child("statistics").child("users").get().val()
        if today not in statistics.keys():
            new_log = {
                name: 0
            }
        elif name not in statistics[today].keys():
            new_log = statistics[today]
            new_log[name] = 0
        else:
            new_log = statistics[today]

        new_log[name] = new_log[name] + 1
        db.child("statistics").child("users").update({today: new_log})

    def update_dudu_statistics(self, user_mention):
        today = str(date.today())
        db = self.firebase.database()
        statistics = db.child("dudu_tracker").get().val()
        if today not in statistics.keys():
            new_log = {
                user_mention: 0
            }
        elif user_mention not in statistics[today].keys():
            new_log = statistics[today]
            new_log[user_mention] = 0
        else:
            new_log = statistics[today]

        if new_log[user_mention] >= 3:
            return False

        new_log[user_mention] = new_log[user_mention] + 1
        db.child("dudu_tracker").update({today: new_log})

        return True

    def update_giveaway_statistics(self, key, type, statistic):
        today = str(date.today())
        db = self.firebase.database()
        statistics = db.child("statistics").child("giveaway_statistics").get().val()
        if not isinstance(key, str):
            key = str(key)
        if today not in statistics.keys():
            new_log = {
                key: {
                    "type": type,
                    statistic: 0
                }
            }
        elif key not in statistics[today].keys():
            new_log = statistics[today]
            new_log[key] = {
                "type": type,
                statistic: 0
            }
        elif statistic not in statistics[today][key].keys():
            new_log = statistics[today]
            new_log[key][statistic] = 0
        else:
            new_log = statistics[today]

        new_log[key][statistic] = new_log[key][statistic] + 1
        db.child("statistics").child("giveaway_statistics").update({today: new_log})

    def update_total_ghosted(self, log_key, log_type):
        self.update_giveaway_statistics(log_key, log_type, "ghosted")

    def update_total_sent(self, log_key, log_type):
        self.update_giveaway_statistics(log_key, log_type, "sent")

    def update_total_stale(self, log_key, log_type):
        self.update_giveaway_statistics(log_key, log_type, "stale")

    def update_total_did_not_read(self, log_key, log_type):
        self.update_giveaway_statistics(log_key, log_type, "violation")

    def publish_seed(self, seed, mon_name, partner_name, logged_file):
        timestamp_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        db = self.firebase.database()
        dudu = db.child("dudu")
        seed_check_result = {
            "timestamp": timestamp_utc,
            "seed": seed,
            "partnerName": partner_name,
            "isPublished": "False",
            "logFile": logged_file,
            "mon": mon_name
        }
        dudu.push(seed_check_result)

    def get_published_seeds(self):
        db = self.firebase.database()
        ret = []
        try:
            dudu = db.child("dudu").order_by_child("isPublished").equal_to("False").get().val()
        except IndexError:
            return ret
        for key in dudu:
            ret.append(dudu[key])
            db.child("dudu").child(key).remove()
        return ret

    def add_strawpoll_result(self, result):
        today = str(date.today())
        db = self.firebase.database()
        statistics = db.child("statistics").child("poll_winners").get().val()
        if today not in statistics.keys():
            new_log = {
                result: 0
            }
        elif result not in statistics[today].keys():
            new_log = statistics[today]
            new_log[result] = 0
        else:
            new_log = statistics[today]

        new_log[result] = new_log[result] + 1
        db.child("statistics").child("poll_winners").update({today: new_log})

    def update_offered_species(self, species):
        today = str(date.today())
        db = self.firebase.database()
        statistics = db.child("statistics").child("species_offered").get().val()
        if not isinstance(species, str):
            species = str(species)
        if species == "0":
            species = "egg"
        if today not in statistics.keys():
            new_log = {
                species: 0
            }
        elif species not in statistics[today].keys():
            new_log = statistics[today]
            new_log[species] = 0
        else:
            new_log = statistics[today]

        new_log[species] = new_log[species] + 1
        db.child("statistics").child("species_offered").update({today: new_log})

    def count_unique_users(self):
        statistics = self.firebase.database().child("statistics").child("users").get().val()
        unique_users = []
        total_delivered = 0
        for key in statistics.keys():
            daily_logs = statistics[key]
            for user in daily_logs.keys():
                if user not in unique_users:
                    unique_users.append(user)
                total_delivered += daily_logs[user]

        print(f"Total Users: {len(unique_users)} for overall {total_delivered} trades")

