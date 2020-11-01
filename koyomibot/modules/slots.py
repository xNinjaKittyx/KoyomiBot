import random

from discord.ext import commands

from koyomibot.utility import discordembed as dmbd


class Slots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def slots(self, ctx):
        """ Basic Slot Machine """

        emojis = random.sample(self.bot.emojis, 6)
        slot1 = random.randint(0, 5)
        slot2 = random.randint(0, 5)
        slot3 = random.randint(0, 5)
        final = "||{}|{}|{}||".format(emojis[slot1], emojis[slot2], emojis[slot3])

        embed = dmbd.newembed(ctx.author, "SLOT MACHINE", final)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Slots(bot))
