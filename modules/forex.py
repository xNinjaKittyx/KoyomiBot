
import ujson
from discord.ext import commands

import utility.discordembed as dmbd


class Forex:

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def forex(self, ctx, *, args):
        args = args.split(' ')

        if len(args) == 1:
            base = 'USD'
            if len(args[0]) != 3:
                return
            conversion = args[0].upper()
        elif len(args) == 2:
            if len(args[0]) != 3 or len(args[1]) != 3:
                return
            base = args[0].upper()
            conversion = args[1].upper()
        else:
            return

        async with self.bot.session.get('https://api.fixer.io/latest?base=' + base + '&symbols=' + conversion) as r:
            if r.status != 200:
                self.bot.logger.warning('Could not get info from fixer.io')
                return
            results = await r.json(loads=ujson.loads)
            desc = base + ' to ' + conversion + ' conversion.'
            em = dmbd.newembed(ctx.author, 'Foreign Exchange', desc, 'http://fixer.io/')
            em.set_thumbnail(url='http://fixer.io/img/money.png')
            em.add_field(name='1 ' + base, value=str(results['rates'][conversion]) + ' ' + conversion)
            await ctx.send(embed=em)
            self.bot.cogs['Wordcount'].cmdcount('forex')


def setup(bot):
    """ Setup Forex Module"""
    bot.add_cog(Forex(bot))
