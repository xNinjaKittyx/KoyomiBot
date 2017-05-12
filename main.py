
# Built-in Python Imports
import random

# Required for disocrd.py
from discord.ext import commands

# Databases
import redis

debug = False

redis_db = redis.StrictRedis(host="localhost", port="6379", db=0)
essential_keys = {
    'DiscordToken',
}

nonessential_keys = {
    'Prefix',
    'GoogleMapsAPI',
    'DarkSkyAPI',
    'CleverbotAPI',
    'AnilistID',
    'AnilistSecret',
    'OsuAPI'
}

modules = {
    'modules.admin',
    'modules.anime',
    'modules.comics',
    'modules.info',
    'modules.log',
    'modules.osu',
    'modules.overwatch',
    'modules.pad',
    'modules.random',
    'modules.search',
    'modules.tags',
    'modules.wordcount'

}
prefix = ''
if debug:
    prefix = '>>'
else:
    prefix = redis_db.get('Prefix')
    if prefix is None:
        prefix = '>'
    else:
        prefix = prefix.decode('utf-8')

description = "Huge rewrite for Rin Bot. No Bullshit. Just fun stuff."
bot = commands.Bot(command_prefix=prefix, description=description, pm_help=True)

def checkkeys():
    """ Returns 1 if all keys are satisfied
        Returns 2 if Essential Keys are not given
        Returns 0 if Essential Keys are given, but some keys are missing."""
    # TODO: Host, port should be configurable.
    print("Checking if Discord API Key Exists...")

    for x in essential_keys:
        if redis_db.get(x) is None:
            return 2

    for x in nonessential_keys:
        if redis_db.get(x) is None:
            return 0

    return 1

def changekeys():
    print("Just press enter if you would like to keep that setting as is. ")

    for x in essential_keys:
        apikey = input(x + ": ")
        if not apikey == "":
            redis_db.set(x, str(apikey))

    for x in nonessential_keys:
        apikey = input(x + ": ")
        if not apikey == "":
            redis_db.set(x, str(apikey))

@bot.event
async def on_message(msg):
    if msg.content.startswith(prefix + "guess"):
        return
    if msg.author.bot:
        return
    #if not checks.checkdev(message) and checks.checkignorelist(message, ignore):
    #    return

    # if message.content.startswith(bot.user.mention):
    #     await bot.send_typing(message.channel)
    #     try:
    #         response = cw.say(message.content.split(' ', 1)[1])
    #         await bot.send_message(message.channel,
    #                                message.author.mention + ' ' + response)
    #     except IndexError:
    #         await bot.send_message(message.channel,
    #                                message.author.mention + ' Don\'t give me '
    #                                'the silent treatment.')
    #     return
    await bot.process_commands(msg)


@bot.event
async def on_ready():

    bot.cogs['Log'].output('Logged in as')
    bot.cogs['Log'].output("Username " + bot.user.name)
    bot.cogs['Log'].output("ID: " + bot.user.id)
    url = (
        "https://discordapp.com/api/oauth2/authorize?client_id=" +
        bot.user.id +
        "&scope=bot&permissions=0"
    )
    bot.cogs['Log'].output("Invite Link: " + url)
    # if not discord.opus.is_loaded() and os.name == 'nt':
    #     discord.opus.load_opus("opus.dll")
    #
    # if not discord.opus.is_loaded() and os.name == 'posix':
    #     discord.opus.load_opus("/usr/local/lib/libopus.so")
    # bot.cogs['log'].output("Loaded Opus Library")


if __name__ == "__main__":
    print("LAUNCHING BOT...")
    chkey = checkkeys()
    # if chkey == 1:
    #     choice = input("Would you like to reset any of your APIkeys? (y/n)")
    #     if choice.lower() == 'y':
    #         changekeys()
    if chkey == 0:
        choice = input("You are missing some API Keys. Set APIKeys? (y/n)")
        if choice.lower() == 'y':
            changekeys()
    if chkey == 2:
        print("You are missing essential API Keys. Entering APIKeys Screen.")
        changekeys()
    random.seed()

    for mod in modules:
        try:
            bot.load_extension(mod)
        except ImportError as e:
            print(e)
            print('[WARNING]: Module ' + mod + ' did not load')
    bot.run(redis_db.get('DiscordToken').decode('utf-8'))
