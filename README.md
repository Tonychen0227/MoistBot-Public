# MoistBot overview

MoistBot is a Discord Bot run on a discord server called [Shaymin's Meadow](https://discord.gg/VfKnVvK). The bot was inspired by [SysBot.NET](https://github.com/kwsch/SysBot.NET) and its capabilities, and the popularity of Pokémon giveaways and "seed checks." 

This bot was ran between April 2020 - August 2020. Here are some interesting statistics.

* 52727 Trade Searches were abandoned (no match after 2 minutes), 24919 Successful, 1396 matches were abandoned (no offered poke), 464 matches violated the rules
* `SwShLegendary` was the most popular `Community` category (298 wins), `Battle` the most popular `Items` category (597 wins), `0Atk0SpeQuiet` the most popular `Ditto` category (107 wins)
* 4 most offered Pokemon: Wooloo (2308), Ditto (2234), Eevee (987), Scorbunny (979)
* Most frequent users: 🥇Coote (1107), 🥈Dylan(1088), 🥉Zack(979), NukeDoctor (964) (next highest had only 607!!)
* Most trades per day, per user: 🥇Dylan(170 trades, 2020-05-18), 🥈Coote(166 trades, 2020-06-29), 🥉Dylan(135 trades, 2020-05-19)

# Technical details

* Run on an Amazon EC2 instance, with three instances of `GiveawayClient` targeting three CFW Nintendo Switch consoles in my house
* Written in Python, with linux commands to aid deployment
* Web-app written in Express (not released), hosted on the same EC2 instance ([LINK](http://ec2-54-202-8-87.us-west-2.compute.amazonaws.com:3000/))
* Firebase realtime database was used [snapshot at 08-14-2020 3:36PM PST](snapshot.json)
* Scalable design, `DiscordClient` handles giveaway voting and all Discord activites, `GiveawayClient` handles the delivering of Pokémon and Seed Checks to the end user
 
# Credits
* [ShinySylveon04](https://github.com/ShinySylveon04) and [Abyzab](https://github.com/Abyzab) for helping me with basically everything
* [fishguy6564](https://gitlab.com/fishguy6564) for helping me decipher [lanturn bot](https://gitlab.com/fishguy6564/lanturn-bot-public-source-code), and for providing permission to "borrow" his [NumpadInterpreter.py](https://gitlab.com/fishguy6564/lanturn-bot-public-source-code/-/blob/master/NumpadInterpreter.py) and [PK8.py](https://gitlab.com/fishguy6564/lanturn-bot-public-source-code/-/blob/master/PK8.py), which were copied verbatim, with minor modifications to PK8.py.
* [olliz0r](https://github.com/olliz0r) for providing the community with [sys-botbase](https://github.com/olliz0r/sys-botbase)
* [kwsch](https://github.com/kwsch) for providing the community with [PKHeX](https://github.com/kwsch/PKHeX) and [SysBot.NET](https://github.com/kwsch/SysBot.NET), from which I took some inspiration for [PK8 data structure](https://github.com/kwsch/PKHeX/blob/master/PKHeX.Core/PKM/PK8.cs) and answering some of my qustions
* The team at [MoreBreedingDittos](https://discord.gg/dittos) for being amazing people
