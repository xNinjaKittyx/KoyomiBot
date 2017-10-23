"""  Module for interactions between users """

import random


import utility.discordembed as dmbd
import ujson

from discord.ext import commands


class Interactions:

    def __init__(self, bot):
        self.bot = bot
        self.phrases = [
            'Don\'t they look cute together?',
            'They must really like each other!',
            'Aww :^)',
            'They\'re really cute together.',
            'Comfy~ Comfy~'
        ]
        self.cache = {}

    def get_user(self, ctx, target):

        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = ctx.guild.get_member_named(target)

        if not user:
            return
        return user

    async def get_phrase(self, author, action, target):

        async with self.bot.session.get(
            f'https://api.gfycat.com/v1test/gfycats/search?search_text={action}%20anime&count=100'
        ) as r:
            if r.status != 200:
                raise ConnectionError(f'Could not GET from Gfycat {r.status}')

            response = await r.json(loads=ujson.loads)
            cursor = response['cursor']
            total = response['found']

        number = random.randint(0, min(99, total))

        while True:
            if number < 100:
                gfycats = response['gfycats']
                img = gfycats[number]['gifUrl']
                break
            else:
                url = f'https://api.gfycat.com/v1test/gfycats/search?search_text={action}%20anime&count=100&cursor={cursor}'

                if url in self.cache:
                    response = self.cache[url]
                    cursor = response['cursor']
                    number -= 100
                else:
                    async with self.bot.session.get(url) as r:
                        if r.status != 200:
                            raise ConnectionError(f'Could not GET from Gfycat {r.status}')

                        response = await r.json(loads=ujson.loads)
                        cursor = response['cursor']
                        number -= 100

        if action == 'hug':
            action = 'hugged'
        elif action == 'kiss':
            action = 'kissed'
        elif action == 'cuddle':
            action = 'cuddled with'

        desc = f'{author} {action} {target}. {random.choice(self.phrases)}'
        em = dmbd.newembed(d=desc)
        em.set_image(url=img)
        return em

    @commands.command()
    async def hug(self, ctx, target):
        target = self.get_user(ctx, target)
        if target is None:
            return

        em = await self.get_phrase(ctx.author, 'hug', target)
        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('hug')

    @commands.command()
    async def kiss(self, ctx, target):
        target = self.get_user(ctx, target)
        if target is None:
            return

        em = await self.get_phrase(ctx.author, 'kiss', target)
        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('kiss')

    @commands.command()
    async def cuddle(self, ctx, target):
        target = self.get_user(ctx, target)
        if target is None:
            return

        em = await self.get_phrase(ctx.author, 'cuddle', target)

        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('cuddle')


def setup(bot):
    """ Setup Interactions Module"""
    bot.add_cog(Interactions(bot))
