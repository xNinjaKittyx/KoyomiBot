
import logging
import random
import os

from logging.handlers import TimedRotatingFileHandler

import aiohttp
import aiofiles
import discord
import redis
import ujson

from discord.ext import commands


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
    'modules.musicplayer',
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

example_config = {
    'DiscordToken': '',
    'Prefix': '',
    'GoogleMapsAPI': '',
    'DarkSkyAPI': '',
    'CleverbotAPI': '',
    'AnilistID': '',
    'AnilistSecret': '',
    'OsuAPI': '',
    'DiscordPW': '',
    'DiscordBots': '',
}


class MyClient(commands.AutoShardedBot):

    def __init__(self, *args, **kwargs):

        if not os.path.exists('logs'):
            os.makedirs('logs')

        self.logger = logging.getLogger('KoyomiBot')
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s::%(levelname)s:%(filename)s:%(lineno)d - %(message)s')
        fh = TimedRotatingFileHandler(filename='logs/koyomi.log', when='midnight')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        self.logger.addHandler(sh)

        self.logger.info("Bot Started".center(30).replace(' ', '-'))

        self.logger.info("Initializing Redis Database".center(30).replace(' ', '-'))
        self.redis_db = redis.StrictRedis()
        self.logger.info('Initialized Redis Database'.center(30).replace(' ', '-'))

        self.logger.info("Initializing Config File".center(30).replace(' ', '-'))
        if not os.path.exists('config'):
            os.makedirs('config')

        if not os.path.exists('config/config.json'):
            with open('config/config.json', 'w') as f:
                f.write(ujson.dumps(example_config, indent=4))
            self.logger.error('No Configuration Found.')
            self.logger.error('Please edit the config file and reboot again.')
            raise RuntimeError('No Config Found')
        else:
            with open('config/config.json', 'r') as f:
                self.config = ujson.loads(f.read())

        self.logger.info("Initialized Config File".center(30).replace(' ', '-'))

        prefix = self.config['Prefix']
        self.logger.info(f'Prefix is set: {prefix}')
        super().__init__(*args, command_prefix=prefix, **kwargs)
        self.session = aiohttp.ClientSession(
            loop=self.loop,
            json_serialize=ujson.dumps,
            headers={'User-Agent': 'Koyomi Discord Bot (https://github.com/xNinjaKittyx/KoyomiBot/)'}
        )

        self.load_all_modules()
        self.add_check(discord.ext.commands.guild_only())
        self.logger.info('Starting Bot'.center(30).replace(' ', '-'))
        self.run(self.config['DiscordToken'])

    async def refresh_config(self):
        async with aiofiles.open('config/config.json', mode='r') as f:
            self.config = ujson.loads(await f.read())
            for key in example_config.keys():
                if key not in self.config:
                    self.config[key] = ''

        async with aiofiles.open('config/config.json', mode='w') as f:
            await f.write(ujson.dumps(self.config, indent=4))

    async def ignore_user(self, user):
        pass

    async def ignore_guild(self, user):
        pass

    def load_all_modules(self):
        self.logger.info('Loading all Modules'.center(30).replace(' ', '-'))
        for mod in modules:
            try:
                self.load_extension(mod)
                self.logger.info(f'Load Successful: {mod}')
            except ImportError as e:
                self.logger.warning(e)
                self.logger.warning(f'[WARNING]: Module {mod} did not load')

    async def check_blacklist(self, msg):
        if msg.author.bot:
            return False
        if isinstance(msg.channel, discord.abc.PrivateChannel):
            return False
        if msg.author.id == 298492601756024835:
            # hardcoding blacklist for "GIVEAWAY NETWORK BETA" which uses a userbot for some reason...
            return False
        if msg.content.startswith(self.command_prefix + 'guess'):
            return False
        if not msg.content.startswith(self.command_prefix):
            return False
        return True

    async def on_message(self, msg):
        if await self.check_blacklist(msg):
            await self.process_commands(msg)

    async def on_guild_join(self, guild):
        data = {
            'shard_id': self.shard_id,
            'shard_count': self.shard_count,
            'server_count': len(self.guilds)
        }
        self.logger.info(f'KoyomiBot joined a new guild! {guild}')
        async with self.session.post(
            f'https://discordbots.org/api/bots/{self.user.id}/stats',
            headers={
                'Authorization': self.config['DiscordBots'],
                'Content-Type': 'application/json'
            },
            data=ujson.dumps(data)
        ) as f:
            if f.status != 200:
                self.logger.error(f'Bad Bot Post Status: {f}')
                self.logger.error(await f.json(loads=ujson.loads))
            else:
                self.logger.error('SUCCESS!')

        async with self.session.post(
            f'https://bots.discord.pw/api/bots/{self.user.id}/stats',
            headers={
                'Authorization': self.config['DiscordPW'],
                'Content-Type': 'application/json'
            },
            data=ujson.dumps(data)
        ) as f:
            if f.status != 200:
                self.logger.error(f'Bad Bot Post Status: {f}')
                self.logger.error(await f.json(loads=ujson.loads))
            else:
                self.logger.error('SUCCESS!')

    async def on_ready(self):
        await self.refresh_config()
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
