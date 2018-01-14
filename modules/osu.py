
from urllib import parse

import ujson
import utility.discordembed as dmbd

from discord.ext import commands


class OsuPlayer:

    def __init__(self, player):
        self.id = player["user_id"]
        self.username = player["username"]
        self.c300 = player["count300"]
        self.c100 = player["count100"]
        self.c50 = player["count50"]
        self.playcount = player["playcount"]
        self.ranked = player["ranked_score"]
        self.total = player["total_score"]
        self.pp = player["pp_rank"]
        self.level = player["level"]
        self.pp_raw = player["pp_raw"]
        self.accuracy = player["accuracy"]
        self.count_ss = player["count_rank_ss"]
        self.count_s = player["count_rank_s"]
        self.count_a = player["count_rank_a"]
        self.country = player["country"]
        self.pp_country_rank = player["pp_country_rank"]

    def display(self, author):
        title = self.username
        desc = self.country.upper()
        url = 'https://osu.ppy.sh/u/' + self.username
        em = dmbd.newembed(author, title, desc, url)
        em.add_field(name='Performance', value=self.pp_raw + 'pp')
        em.add_field(name='Accuracy', value="{0:.2f}%".format(float(self.accuracy)))
        lvl = int(float(self.level))
        percent = int((float(self.level) - lvl) * 100)
        em.add_field(name='Level', value="{0} ({1}%)".format(lvl, percent))
        em.add_field(name='Rank', value=self.pp)
        em.add_field(name='Country Rank', value=self.pp_country_rank)
        em.add_field(name='Playcount', value=self.playcount)
        em.add_field(name='Total Score', value=self.total)
        em.add_field(name='Ranked Score', value=self.ranked)
        return em


class Osu:

    def __init__(self, bot):
        self.bot = bot

    async def getlink(self, mode, playername):
        cookiezi = self.bot.config['OsuAPI']
        link = f'http://osu.ppy.sh/api/get_user?k={cookiezi}&u={playername}&m={mode}'

        async with self.bot.session.get(link) as r:
            if r.status != 200:
                self.bot.logger.warning('Peppy Failed')
                return
            j = await r.json(loads=ujson.loads)
            return j[0]

    @commands.command()
    async def osu(self, ctx, *, name: str):
        name = parse.quote(name)
        player = OsuPlayer(await self.getlink(0, name))
        em = player.display(ctx.author)
        em.set_image(url=f"http://lemmmy.pw/osusig/sig.php?colour=hex66ccff&uname={name}&mode=0")

        await ctx.send(embed=em)
        await self.bot.cogs['Wordcount'].cmdcount('osu')

    @commands.command()
    async def taiko(self, ctx, *, name: str):
        player = OsuPlayer(await self.getlink(1, name))
        em = player.display(ctx.author)
        em.set_image(url=f"http://lemmmy.pw/osusig/sig.php?colour=hex66ccff&uname={name}&mode=1")

        await ctx.send(embed=em)
        await self.bot.cogs['Wordcount'].cmdcount('taiko')

    @commands.command()
    async def ctb(self, ctx, *, name: str):
        player = OsuPlayer(await self.getlink(2, name))
        em = player.display(ctx.author)
        em.set_image(url=f"http://lemmmy.pw/osusig/sig.php?colour=hex66ccff&uname={name}&mode=2")

        await ctx.send(embed=em)
        await self.bot.cogs['Wordcount'].cmdcount('ctb')

    @commands.command()
    async def mania(self, ctx, *, name: str):
        player = OsuPlayer(await self.getlink(3, name))
        em = player.display(ctx.author)
        em.set_image(
            url=f"http://lemmmy.pw/osusig/sig.php?colour=hex66ccff&uname={name}&mode=3")

        await ctx.send(embed=em)
        await self.bot.cogs['Wordcount'].cmdcount('mania')


def setup(bot):
    bot.add_cog(Osu(bot))
