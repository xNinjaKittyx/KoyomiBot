
# Built-in Python Imports
import logging
from logging.handlers import TimedRotatingFileHandler
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
    'modules.forex',
    'modules.info',
    'modules.interactions',
    'modules.log',
    'modules.mail',
    # 'modules.musicplayer',
    'modules.musicplayer_rewrite',
    'modules.osu',
    'modules.overwatch',
    'modules.pad',
    'modules.profile',
    'modules.random',
    'modules.search',
    'modules.slots',
    'modules.tags',
    'modules.todo',
    'modules.weather',
    'modules.wordcount'

}


class MyClient(commands.AutoShardedBot):

    def __init__(self, *args, **kwargs):

        self.logger = logging.getLogger('KoyomiBot')
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s]: %(message)s')
        if not os.path.exists('logs'):
            os.makedirs('logs')
        fh = TimedRotatingFileHandler(filename='logs/koyomi.log', when='midnight')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        self.logger.addHandler(sh)
        self.redis_db = redis.StrictRedis()
        self.debug = bool(kwargs.pop('debug', False))

        self.logger.info("LAUNCHING BOT...")
        self.logger.info('Initialized Redis Database')
        prefix = self.redis_db.get('Prefix')
        if prefix is None:
            prefix = '.koyomi'
        else:
            prefix = prefix.decode('utf-8')
        self.logger.info(f'Prefix is set: {prefix}')
        super().__init__(*args, command_prefix=prefix, **kwargs)
        import ujson
        self.session = aiohttp.ClientSession(loop=self.loop,
                                             json_serialize=ujson.dumps,
                                             headers={'User-Agent': 'Koyomi Discord Bot (https://github.com/xNinjaKittyx/KoyomiBot/)'})

        self.logger.info('Checking For Keys')

        setkeys = bool(kwargs.pop('setkeys', False))
        if setkeys:
            self.set_keys()
        self.check_keys()
        self.load_all_modules()
        self.add_check(discord.ext.commands.guild_only())
        self.logger.info('Starting Bot')
        self.run(self.redis_db.get('DiscordToken').decode('utf-8'))

    def load_all_modules(self):
        self.logger.info('Loading all Modules')
        for mod in modules:
            try:
                self.load_extension(mod)
                self.logger.info(f'Load Successful: {mod}')
            except ImportError as e:
                self.logger.warning(e)
                self.logger.warning(f'[WARNING]: Module {mod} did not load')

    def check_keys(self):
        for x in essential_keys:
            if self.redis_db.get(x) is None:
                self.logger.critical(f'{x} key is missing. Please set it')
                quit()
        for x in nonessential_keys:
            if self.redis_db.get(x) is None:
                self.logger.warning(f'{x} key is missing. Some functions may not work properly.')

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
        if isinstance(msg.channel, discord.abc.PrivateChannel):
            return
        if msg.content.startswith(self.command_prefix + 'guess'):
            return
        if msg.author.bot:
            return

        await self.process_commands(msg)

    async def on_ready(self):
        random.seed()
        self.logger.info('Logged in as')
        self.logger.info(f"Username {self.user.name}")
        self.logger.info(f"ID: {self.user.id}")
        url = f"https://discordapp.com/api/oauth2/authorize?client_id={self.user.id}&scope=bot&permissions=0"
        self.logger.info(f"Invite Link: {url}")
        try:
            if not discord.opus.is_loaded() and os.name == 'nt':
                discord.opus.load_opus("libopus0.x64.dll")

            if not discord.opus.is_loaded() and os.name == 'posix':
                discord.opus.load_opus("/usr/local/lib/libopus.so")
            self.logger.info("Loaded Opus Library")
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("Opus library did not load. Voice may not work.")


if __name__ == "__main__":
    description = 'KoyomiBot: Lots of Fun, Minimal Moderation, No bullshit, SFW.'
    bot = MyClient(description=description, pm_help=True, setkeys=False,
                   game=discord.Game(name='https://xninjakittyx.github.io/KoyomiBot/',
                                     url='https://xninjakittyx.github.io/KoyomiBot/',
                                     type=1))
