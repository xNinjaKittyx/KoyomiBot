
import asyncio
import random

import discord
from discord.ext import commands
import utility.discordembed as dmbd


class Profile:
    def __init__(self, bot):
        self.bot = bot
        self.redis_db = redis.StrictRedis(host="localhost", port="6379", db=0)
        """ So in this section, there's going to be some way of having "points"
        and therefore leveling up after reaching x number of points.

        First we need to set some sort of leveling system.

        exp curve. Start with 100, then increase x^1.8 per leve

        base_xp * (level_to_get ^ factor) = exp required for level_to_get


        sqrt(expreq / base_xp, factor) = level_to_get

        1) Avatar. If someone looks you up, you can get a small exp between 1 - 5
        2) Chatting? Maybe each message will give you 0.1 exp?
        3) Perhaps a game where you bet any available exp. Lowstakes, highstakes.
        lowstakes will give you 1.25x exp back, but high stake will give you 1.5x back...
        Expected value of lowstake (50%) will be 0.625x exp...
        Expected Value of highstake (33%) will be 0.495x exp..

        """

    async on_message(self, msg):
        pass # give em sum xp fam :D

    @commands.command(pass_context=True)
    async def avatar(self, ctx, *, name: str):
        """ Grabbing an avatar of a person """
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = ctx.message.server.get_member_named(name)
        if not user:
            name = name.lower()
            for x in ctx.message.server.members:
                if x.name.lower() == name:
                    user = x
                elif x.nick:
                    if x.nick.lower() == name:
                        user = x

        if not user:
            return
        author = ctx.message.author
        em = dmbd.newembed(author, u=user.avatar_url)
        em.set_image(url=user.avatar_url)
        grade = random.randint(1,11)
        em.add_field(name=user.name + '#' + user.discriminator + '\'s Avatar', value="Sugoi :D")

        if author != user:
            pass # GIVE EM SUM XP FAM

        await self.bot.say(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('avatar')

    @commands.command(pass_context=True)
    async def profile(self, ctx, *,  name: str):
        """ Display Profile :o """
        pass
