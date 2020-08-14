from FirebaseService import FirebaseService


class StringCreator:
    def __init__(self):
        self.firebase = FirebaseService()

    def get_giveaway_announcement(self, current_giveaway, clients):
        base_string = ""
        if len(clients) == 0:
            clients = "No hosts at the moment, **bot probably broke**"
        else:
            clients = ','.join(clients)
        link_code = current_giveaway['linkCode']
        timestamp = current_giveaway['timestampString']
        duration = current_giveaway['totalDurationMins']
        bucket = current_giveaway['bucket']
        category = current_giveaway['category']

        base_string += (f"Giveaway time!\n"
                        f"Your hosts: {clients}\n"
                        f"Link code: {link_code}\n"
                        f"Double dipping allowed: Yes dip any amount of times the bot won't be offended\n"
                        f"Start time (UTC): {timestamp}\n"
                        f"Duration (mins): {duration}\n\n"
                        f"Pokemon info: Category {category} from collection {bucket}\n"
                        f"For more information, see: http://ec2-54-202-8-87.us-west-2.compute.amazonaws.com:3000/\n"
                        f"RULES!\n"
                        f"No trading trade evos, or variants of trade evos (e.g. galarian slowpoke)\n"
                        f"No taking back the Pokemon or the bot will quit on you\n"
                        f"You must offer a pokemon within 20 seconds or the bot will quit on you\n"
                        f"If double dipping is **not** allowed, you must offer a Pokemon OT'd by you\n"
                        f"**Please give others time to block you!** To block press down either stick like a button\n"
                        f"Please vote on the next CATEGORY for next giveaway: "
                        f"<https://www.strawpoll.me/{current_giveaway['strawpoll']}>")

        return base_string

    def get_dudu_announcement(self, dudu):
        partner_name = dudu['partnerName']
        mon = dudu['mon']
        seed = dudu['seed']
        timestamp = dudu['timestamp']
        return (f"Seed check for {partner_name}\n"
                f"Offered mon: {mon}\n"
                f"Seed: {seed}\n"
                f"Timestamp: {timestamp}\n"
                f"Find spawns: https://leanny.github.io/seedchecker/index.html\n"
                f"If there are any seed errors, here is your pk8 file so you can calc the seed that way also.")
