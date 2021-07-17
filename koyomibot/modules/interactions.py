"""  Module for interactions between users """

import logging
import random

from discord.ext import commands

import koyomibot.utility.discordembed as dmbd

logger = logging.getLogger(__name__)


class Interactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

    def get_user(self, ctx, target):

        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = ctx.guild.get_member_named(target)
        if not user:
            logger.info(f"Could not find {target}")
        return user

    async def get_phrase(self, author, action, target, positive):

        async with self.bot.session.get(
            f"https://api.gfycat.com/v1/gfycats/search?search_text={action}%20anime&count=100"
        ) as r:
            if r.status != 200:
                raise ConnectionError(f"Could not GET from Gfycat {r.status}")

            response = await r.json()

        total = response["found"]

        number = random.randint(0, min(99, total))

        gfycats = response["gfycats"]
        img = gfycats[number]["gifUrl"]

        if action == "hug":
            action = "hugged"
        elif action == "kiss":
            action = "kissed"
        elif action == "cuddle":
            action = "cuddled with"
        elif action == "slap":
            action = "slapped"
        elif action == "punch":
            action = "punched"
        else:
            raise ValueError("invalid action")

        desc = f"{author.display_name} {action} {target.display_name}."
        em = dmbd.newembed(d=desc)
        em.set_image(url=img)
        return em

    @commands.command()
    async def hug(self, ctx, target):
        target = self.get_user(ctx, target)
        if target is None:
            return

        em = await self.get_phrase(ctx.author, "hug", target, True)
        await ctx.send(embed=em)

    @commands.command()
    async def kiss(self, ctx, target):
        target = self.get_user(ctx, target)
        if target is None:
            return

        em = await self.get_phrase(ctx.author, "kiss", target, True)
        await ctx.send(embed=em)

    @commands.command()
    async def cuddle(self, ctx, target):
        target = self.get_user(ctx, target)
        if target is None:
            return

        em = await self.get_phrase(ctx.author, "cuddle", target, True)
        await ctx.send(embed=em)

    @commands.command()
    async def slap(self, ctx, target):
        target = self.get_user(ctx, target)
        if target is None:
            return

        em = await self.get_phrase(ctx.author, "slap", target, True)
        await ctx.send(embed=em)

    @commands.command()
    async def punch(self, ctx, target):
        target = self.get_user(ctx, target)
        if target is None:
            return

        em = await self.get_phrase(ctx.author, "punch", target, True)
        await ctx.send(embed=em)


def setup(bot):
    """Setup Interactions Module"""
    bot.add_cog(Interactions(bot))
