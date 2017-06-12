
# Built-in Python Imports
import random
import os

# Required for disocrd.py
import aiohttp
import discord
from discord.ext import commands

# Databases
import redis


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
    'modules.animehangman',
    'modules.cleverbot',
    'modules.comics',
    'modules.info',
    'modules.log',
    # 'modules.musicplayer',
    'modules.osu',
    'modules.overwatch',
    'modules.pad',
    'modules.profile',
    'modules.random',
    'modules.search',
    'modules.slots',
    'modules.tags',
    'modules.weather',
    'modules.wordcount'

}


class MyClient(commands.AutoShardedBot):

    def __init__(self, *args, **kwargs):
        self.redis_db = redis.StrictRedis()
        self.debug = bool(kwargs.pop('debug', False))
        print('Initialized Redis Database')
        prefix = self.redis_db.get('Prefix')
        if prefix is None:
            prefix = '.koyomi'
        else:
            prefix = prefix.decode('utf-8')
        print('Prefix is set: ' + prefix)
        super().__init__(*args, command_prefix=prefix, **kwargs)
        self.session = aiohttp.ClientSession(loop=self.loop)

        print('Checking For Keys')

        setkeys = bool(kwargs.pop('setkeys', False))
        if setkeys:
            self.set_keys()
        self.check_keys()
        self.load_all_modules()
        print('Starting Bot')
        self.run(self.redis_db.get('DiscordToken').decode('utf-8'))

    def load_all_modules(self):
        print('Loading all Modules')
        for mod in modules:
            try:
                self.load_extension(mod)
                print('Load Successful: ' + mod)
            except ImportError as e:
                print(e)
                print('[WARNING]: Module ' + mod + ' did not load')

    def check_keys(self):
        for x in essential_keys:
            if self.redis_db.get(x) is None:
                raise NameError(x + ' key is missing. Please set it')
                quit()
        for x in nonessential_keys:
            if self.redis_db.get(x) is None:
                print(x + ' key is missing. Some functions may not work properly.')

    def set_keys(self):
            print('SetKeys was activated. Going through key setup.')
            print('Just press enter if you would like to keep the key the same as before.')
            for x in essential_keys:
                apikey = input(x + ": ")
                if not apikey == "":
                    self.redis_db.set(x, str(apikey))

            for x in nonessential_keys:
                apikey = input(x + ": ")
                if not apikey == "":
                    self.redis_db.set(x, str(apikey))

    async def on_message(self, msg):
        if msg.content.startswith(self.command_prefix + 'guess'):
            return
        if msg.author.bot:
            return

        await self.process_commands(msg)

    async def on_ready(self):
        random.seed()
        self.cogs['Log'].output('Logged in as')
        self.cogs['Log'].output("Username " + self.user.name)
        self.cogs['Log'].output("ID: " + str(self.user.id))
        url = (
            "https://discordapp.com/api/oauth2/authorize?client_id=" +
            str(self.user.id) +
            "&scope=bot&permissions=0"
        )
        self.cogs['Log'].output("Invite Link: " + url)
        try:
            if not discord.opus.is_loaded() and os.name == 'nt':
                discord.opus.load_opus("libopus0.x64.dll")

            if not discord.opus.is_loaded() and os.name == 'posix':
                discord.opus.load_opus("/usr/local/lib/libopus.so")
            self.cogs['Log'].output("Loaded Opus Library")
        except:
            self.cogs['Log'].output("Opus library did not load. Voice may not work.")


if __name__ == "__main__":
    print("LAUNCHING BOT...")
    description = 'KoyomiBot: Lots of Fun, Minimal Moderation, No bullshit, SFW.'
    bot = MyClient(description=description, pm_help=True, setkeys=False)
