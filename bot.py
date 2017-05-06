import asyncio
import json
import logging
import random
import os
import time
import sys

import discord
import requests
import tools.checks as checks
import tools.discordembed as dmbd
from discord.ext import commands
from discord.utils import find
from cleverwrap import CleverWrap
from PIL import Image
import log


__author__ = "Daniel Ahn"
__version__ = "0.6"
name = "BakaBot"


# Creating files if they do not exist.
# ignore.json is the list of ignored channels, servers, users
# setup.json includes all the API keys
if not os.path.exists('./json'):
    os.makedirs('./json')
if not os.path.isfile('./json/ignore.json'):
    with open('./json/ignore.json', 'w',) as outfile:
        json.dump({"servers": [], "channels": [], "users": []},
                  outfile, indent=4)
with open('./json/ignore.json') as data_file:
    ignore = json.load(data_file)

if not os.path.isfile('./json/setup.json'):
    with open('./json/setup.json', 'w',) as outfile:
        json.dump({u"botkey": None,
                   u"GoogleAPIKey": None,
                   u"DarkSkyAPIKey": None,
                   u"CleverbotAPI": None,
                   u"AnilistID": None,
                   u"AnilistSecret": None,
                   u"Prefix": u"~"},
                  outfile, indent=4)
with open('./json/setup.json') as data_file:
    settings = json.load(data_file)


# Setting up basic logging. Honestly I don't have much use for this
# I use another logger to log commands used and etc.
logging.basicConfig(filename='rin.log', level=logging.WARNING)

logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='../discord.log',
                              encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s: \
                                        %(name)s: %(message)s'))
logger.addHandler(handler)


# Seeding the random, activating cleverbot. Creating bot class.
random.seed()
if settings["CleverbotAPI"]:
    try:
        cw = CleverWrap(settings["CleverbotAPI"])
    except:
        log.output("CleverbotAPIKey was not accepted.")
else:
    log.output("No CleverBotAPI was Provided")


# List of Modules used.
modules = {
    'modules.anime',
    'modules.cat',
    'modules.comics',
    'modules.fun',
    'modules.gfycat',
    'modules.info',
#    'modules.musicplayer',
    'modules.osu',
    'modules.overwatch',
#    'modules.pad',
#    'modules.ranks',
#    'modules.safebooru',
#    'modules.weather',
    'modules.wordDB',
#    'modules.XDCC'
    'modules.animehangman'

}



def checkignorelistevent(chan):
    # checkignorelist given a channel.
    for serverid in ignore["servers"]:
        if serverid == chan.server.id:
            return True

    for channelid in ignore["channels"]:
        if channelid == chan.id:
            return True



@bot.command(hidden=True)
async def testembed():
    title = 'My Embed Title'
    desc = 'My Embed Description'
    em = dmbd.newembed(bot.user, title, desc)
    em.set_image(url="https://myanimelist.cdn-dena.com/images/anime/3/67177.jpg")
    em.set_thumbnail(url="http://wiki.faforever.com/images/e/e9/Discord-icon.png")
    em.add_field(name="wololol", value='[ohayo](http://www.google.com)')
    em.add_field(name=":tururu:", value="wtf")
    em.add_field(name="wololol", value="wtf")
    em.add_field(name="imgay", value="baka", inline=False)
    em.add_field(name="imgay", value="baka", inline=False)
    em.add_field(name="imgay", value="baka", inline=False)
    await bot.say(embed=em)




@bot.event
async def on_member_join(member):
    await bot.send_message(member, "Welcome to {0}! Type ~normie in #openthegates to enter the server!".format(member.server.name))



@bot.event
async def on_member_remove(member):
    await bot.send_message(member.server.default_channel, '{} has left the server.'.format(member.name))
