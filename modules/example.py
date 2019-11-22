import logging

from discord.ext import commands

from main import MyClient


log = logging.getLogger(__name__)


class Example(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot


def setup(bot: MyClient) -> None:
    bot.add_cog(Example(bot))
