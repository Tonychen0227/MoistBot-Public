import discord
from FirebaseService import FirebaseService
from StrawpollService import StrawpollService
from datetime import datetime, timedelta
import os
import dotenv
import asyncio
from StringCreator import StringCreator
import traceback


class DiscordClient(discord.Client):
    def __init__(self, guild):
        super().__init__()
        self.guild_string = guild
        self.guild = None
        self.giveaway = None
        self.raids = None
        self.bot_spam = None
        self.running_giveaway = False
        self.giveaway_message = None
        self.poll_message = None
        self.mods = []
        self.ditto_giveaway_role = None
        self.firebase_service = FirebaseService()
        self.strawpoll_service = StrawpollService()
        self.last_status_check = datetime.utcnow()
        self.last_user_status_check = datetime.utcnow()
        self.string_creator = StringCreator()
        self.ga_duration_minutes = 20
        self.is_looping = False

    def __del__(self):
        self.firebase_service.stop_current_giveaway()
        self.remove_giveaway_message()

    async def on_ready(self):
        guild = discord.utils.get(self.guilds, name=self.guild_string)
        print(
            f'{self.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})', flush=True
        )
        self.guild = guild
        giveaway = discord.utils.get(self.guild.channels, name="giveaway-announcements")
        self.giveaway = giveaway
        async for x in giveaway.history():
            if str(x.author) == "MoistBot#4929":
                await x.delete()
        bot_spam = discord.utils.get(self.guild.channels, name="bot-test")
        self.bot_spam = bot_spam
        raids = discord.utils.get(self.guild.channels, name="raid-seed-checking")
        self.raids = raids
        ditto_giveaway_role = discord.utils.get(self.guild.roles, name="Ditto Giveaway")
        self.ditto_giveaway_role = ditto_giveaway_role
        mod_role = discord.utils.get(self.guild.roles, name="Moderator")
        self.mods = mod_role.members
        admin_role = discord.utils.get(self.guild.roles, name="Admin")
        # Look for MYSELF
        helper_role = discord.utils.get(self.guild.roles, name="Resident Hackerman")
        for member in helper_role.members:
            if str(member) == "xSLAY3RL0Lx#0630":
                self.mods.append(member)
                break
        self.mods.append(admin_role.members)
        self.giveaway_message = None
        self.poll_message = None

    async def send_giveaway_message(self, message_content):
        self.giveaway_message = await self.giveaway.send(message_content)

    async def update_giveaway_message(self, message_content):
        if self.giveaway_message is not None:
            await self.giveaway_message.edit(content=message_content)
        else:
            self.giveaway_message = await self.giveaway.send(message_content)

    async def remove_giveaway_message(self):
        if self.giveaway_message is not None:
            await self.giveaway_message.delete()
            self.giveaway_message = None
        if self.poll_message is not None:
            await self.poll_message.delete()
            self.poll_message = None

    def generate_ga_message(self, current_giveaway, clients):
        last_ping_timestamp = self.firebase_service.get_last_ping_timestamp()
        timestamp = int(datetime.timestamp(datetime.utcnow()))
        base_string = ""
        if timestamp > last_ping_timestamp + timedelta(hours=2).seconds:
            base_string = f"{self.ditto_giveaway_role.mention}\n"
            self.firebase_service.update_last_ping_timestamp()

        base_string += self.string_creator.get_giveaway_announcement(current_giveaway, clients)

        return base_string

    async def send_help(self, channel):
        await channel.send(f"Available options!\n"
                           f"`^start` to begin running the bot\n"
                           f"`^stop` to kill the bot \n"
                           f"`^setDuration <duration>` to update minutes each GA runs for (minimum 10)\n"
                           f"`^status` for a status check (EVERYONE)\n")

    async def send_status(self, channel):
        await channel.send(f"```STATUS CHECK DING DING DING\n"
                           f"Currently active: {self.running_giveaway}\n"
                           f"Giveaway duration (mins): {self.ga_duration_minutes}\n"
                           f"This message will only be sent every minute```")

    async def refresh_giveaway_message(self):
        current_giveaway = self.firebase_service.get_current_giveaway()[1]
        if not current_giveaway["isOver"]:
            clients = self.firebase_service.get_current_giveaway_clients()
            message = self.generate_ga_message(current_giveaway, clients)
            await self.update_giveaway_message(message)

    async def make_new_giveaway(self, current_giveaway):
        await self.remove_giveaway_message()
        self.firebase_service.stop_current_giveaway()

        strawpoll_result = self.strawpoll_service.get_popular_option(current_giveaway["strawpoll"])

        current_giveaway["nextCategory"] = strawpoll_result
        current_giveaway["nextSpecies"] = ""

        self.firebase_service.add_strawpoll_result(strawpoll_result)

        new_giveaway = self.firebase_service.create_giveaway(self.ga_duration_minutes,
                                                             current_giveaway["nextTheme"]["bucket"],
                                                             current_giveaway["nextCategory"],
                                                             current_giveaway["nextSpecies"])

        clients = self.firebase_service.get_current_giveaway_clients()
        message = self.generate_ga_message(new_giveaway, clients)

        await self.send_giveaway_message(message)

    async def handle_giveaway_updates(self):
        if not self.running_giveaway:
            return
        current_giveaway = self.firebase_service.get_current_giveaway()[1]
        current_epoch_ms = int(datetime.timestamp(datetime.utcnow()))
        current_giveaway_duration = current_giveaway["totalDurationMins"]
        new_giveaway_threshold = current_giveaway["epochTimestamp"] + timedelta(
            minutes=current_giveaway_duration).seconds

        if current_epoch_ms > new_giveaway_threshold or current_giveaway["isOver"]:
            await self.make_new_giveaway(current_giveaway)
            return

        await self.refresh_giveaway_message()

    async def handle_dudu_updates(self):
        if self.raids is None:
            return
        dudus = self.firebase_service.get_published_seeds()
        for dudu in dudus:
            announcement = self.string_creator.get_dudu_announcement(dudu)
            with open(f'logged_pk_files/{dudu["logFile"]}.pk8', 'rb') as mon_file:
                await self.raids.send(announcement, file=discord.File(mon_file, 'your_mon.pk8'))

    async def handle_dudu_queue(self):
        queue = self.firebase_service.dudu_get_queue()
        if queue is None:
            return
        for queued in queue:
            if queued["taken"] != "False":
                if "visited" not in queued.keys() or not queued["visited"]:
                    self.firebase_service.dudu_set_visited(queued["name"])
                else:
                    self.firebase_service.dudu_remove_from_queue(queued["name"])
                    await self.raids.send(f"{queued['name']} BOT {queued['taken']} is serving you you have 2 mins")

    async def dm_user(self, member, message):
        dm_channel = await member.create_dm()
        await dm_channel.send(message)

    async def on_message(self, message):
        if not self.is_looping:
            print("regenerating loop", flush=True)
            self.loop.create_task(handle_continuous_updates())

        if message.channel == self.bot_spam and message.author != self.user and message.author in self.mods:
            if message.content == "^start":
                self.running_giveaway = True

            elif message.content == "^stop":
                self.firebase_service.stop_current_giveaway()
                await self.remove_giveaway_message()
                self.running_giveaway = False

            elif len(message.content) > 1 and message.content.split()[0] == "^setDuration":
                request = int(message.content.split()[1])
                if request > 10:
                    self.ga_duration_minutes = request

            elif message.content == "^help":
                await self.send_help(message.channel)

            elif message.content == "^status":
                await self.send_status(message.channel)

        if message.channel != self.bot_spam and message.content == "^status" \
                and self.last_user_status_check + timedelta(minutes=1) < datetime.utcnow():
            self.last_user_status_check = datetime.utcnow()
            await self.send_status(message.channel)

        if message.channel == self.raids:
            if message.content == "^join":
                result = self.firebase_service.dudu_get_place_in_queue(message.author.mention)
                if result != -1:
                    await self.dm_user(message.author,
                                       (
                                           f"You are already in queue; your place is no. {result} in the queue...\n"
                                           f"Bot will ping you when it is searching"))
                else:
                    has_chatot = False
                    for role in message.author.roles:
                        if role.name == "Chatot" or role.name == "Noivern":
                            has_chatot = True

                    clients = self.firebase_service.get_current_giveaway_clients()

                    if len(clients) == 0:
                        response = "No hosts at the moment, **bot probably broke**, refer to post in #giveaway_announcements"
                    elif not self.running_giveaway:
                        response = "Join failed! Bots are currently not running"
                    else:
                        enqueued_result = self.firebase_service.dudu_enqueue(message.author.mention, has_chatot)
                        if not enqueued_result:
                            response = "Join failed! Non-Chatots are limited to three queue joins a day."
                        else:
                            response = (f"You have joined queue! Your link code is {enqueued_result['linkCode']}\n"
                                        f"Bot will ping you when it is searching")
                    await self.dm_user(message.author, response)

            elif message.content == "^check":
                result = self.firebase_service.dudu_get_place_in_queue(message.author.mention)
                await self.dm_user(message.author,
                                   (
                                       f"Your place is no. {result} in the queue\n"
                                       f"Bot will ping you when it is searching"))

        if not self.running_giveaway:
            return


if __name__ == '__main__':
    dotenv.load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD = os.getenv('DISCORD_GUILD')
    discord_client = DiscordClient(GUILD)

    async def handle_continuous_updates():
        while not discord_client.is_closed():
            print(f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} routine checks", flush=True)
            discord_client.is_looping = True
            try:
                await discord_client.handle_giveaway_updates()
                await discord_client.handle_dudu_updates()
                await discord_client.handle_dudu_queue()
            except Exception as e:
                print(f"exception, {e}", flush=True)
                print(traceback.format_exc(), flush=True)
                discord_client.is_looping = False
                print("quit loop", flush=True)
                return
            await asyncio.sleep(10)  # task runs every 10 seconds

    discord_client.loop.create_task(handle_continuous_updates())
    discord_client.run(TOKEN)
