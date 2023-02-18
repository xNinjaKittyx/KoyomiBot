import random

from discord.commands import slash_command
from discord.ext import commands

from koyomibot.utility.allowed_guilds import ALLOWED_GUILDS


class Jon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jon_quotes = [
            "oh",
            "what",
            "oh my god dan",
            "i shouldve done cs",
            "ee is a dumpster fire",
            "STEM was a mistake",
            "i hate semiconductors",
            "HE RUSHED B",
            "dude actually tho",
            "w\ne\nl\np\nlol",
            "que",
        ]
        self.wanny_quotes = [
            "just don't!",
            "op",
            "T.T",
            "iono",
            "o.o",
            "who the heck is that",
            "holy moly",
            "🙁",
            "ur the one who's boosted",
            "rip",
            "its impossible",
            "that's too hard",
            "wao dan too good",
            "not too hardo",
            "so turns out...",
            "so wheres my peoples",
            "its my bedtime",
            "das rite",
            "where r my peeple",
            "not enough sodium",
        ]

    @slash_command(guild_ids=ALLOWED_GUILDS)
    async def jon(self, ctx):
        """Some stupid command for quoting some dude"""
        await ctx.respond(random.choice(self.jon_quotes))

    @slash_command(guild_ids=ALLOWED_GUILDS)
    async def wanny(self, ctx):
        """Some stupid command for quoting some dude"""
        await ctx.respond(random.choice(self.wanny_quotes))


def setup(bot):
    bot.add_cog(Jon(bot))
