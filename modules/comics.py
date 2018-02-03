
import random
import re

import ujson

from bs4 import BeautifulSoup
from discord.ext import commands

from utility import discordembed as dmbd
from utility.redis import redis_pool


class Comics:
    def __init__(self, bot):
        self.bot = bot

    async def refreshxkcd(self):
        if await redis_pool.get('xkcdmax') is not None:
            return True
        async with self.bot.session.get("http://xkcd.com/info.0.json") as r:
            if r.status != 200:
                self.bot.logger.warning("XKCD is down")
                return False
            j = await r.json(loads=ujson.loads)
            await redis_pool.set('xkcdmax', j['num'], expire=86400)
            return True

    async def getxkcd(self, num, url):
        """ Num should be passed as an INT """
        num = int(num)
        result = await redis_pool.hget('xkcd', num)
        if result is None:
            async with self.bot.session.get(url + "/info.0.json") as r:
                if not r.status == 200:
                    self.bot.logger.warning("Unable to get XKCD #" + str(num))
                    return
                j = await r.json(loads=ujson.loads)
                await redis_pool.hmset('xkcd', {num: j})
                return j
        else:
            j = result.decode('utf-8')
            j = ujson.loads(j)
            return j

    @commands.command()
    async def xkcd(self, ctx):
        """Gives a random XKCD Comic"""
        chk = await self.refreshxkcd()
        if not chk:
            return
        maxnum = int((await redis_pool.get('xkcdmax')).decode('utf-8'))
        number = random.randint(1, maxnum)
        url = "http://xkcd.com/" + str(number)
        j = await self.getxkcd(number, url)

        em = dmbd.newembed(ctx.author, j['safe_title'], u=url)
        em.set_image(url=j['img'])
        em.add_field(name=j['alt'], value="{0}/{1}/{2}".format(j['month'], j['day'], j['year']))
        await ctx.send(embed=em)
        await self.bot.cogs['Wordcount'].cmdcount('xkcd')

    async def refreshcyanide(self):
        if await redis_pool.get('cyanidemax') is not None:
            return True
        async with self.bot.session.get("http://explosm.net/comics/latest") as r:
            if r.status != 200:
                self.bot.logger.warning("Cyanide&Happiness is down")
                return False
            soup = BeautifulSoup(await r.text(), 'html.parser')
            current = int(re.findall(r'\d+', soup.find(id="permalink", type="text").get("value"))[0])
            await redis_pool.set('cyanidemax', current, ex=86400)
            return True

    async def getcyanide(self, num, url):
        num = int(num)
        result = await redis_pool.hget('cyanide', num)
        if result is None:
            async with self.bot.session.get(url) as r:
                if not r.status == 200:
                    self.bot.logger.warning("Unable to get Cyanide #" + str(num))
                    return
                soup = BeautifulSoup(await r.text(), 'html.parser')
                if soup.prettify().startswith('Could not'):
                    await self.bot.send('Report this number as a dead comic: ' + str(num))
                    return
                img = 'http:' + str(soup.find(id="main-comic")['src'])
                await redis_pool.hmset('xkcd', {num: img})
                return img
        else:
            img = result.decode('utf-8')
            return img

    @commands.command()
    async def cyanide(self, ctx):
        """ Gives a random Cyanide & Happiness Comic"""
        chk = await self.refreshcyanide()
        if not chk:
            return

        # whatever reason, comics 1 - 38 don't exist.
        number = random.randint(39, int((await redis_pool.get('cyanidemax')).decode('utf-8')))
        link = 'http://explosm.net/comics/' + str(number)

        img = await self.getcyanide(number, link)
        if img is None:
            return
        em = dmbd.newembed(ctx.author, 'Cyanide and Happiness', str(number), u=link)
        em.set_image(url=img)
        await ctx.send(embed=em)
        await self.bot.cogs['Wordcount'].cmdcount('cyanide')

    @commands.command()
    async def cyanidercg(self, ctx):
        """ Gives a randomly generated Cyanide & Happiness Comic"""

        async with self.bot.session.get('http://explosm.net/rcg') as r:
            if not r.status == 200:
                self.bot.logger.warning("Unable to get RCG for Cyanide")
                return
            soup = BeautifulSoup(await r.text(), 'html.parser')
            img = 'http:' + str(soup.find(id='rcg-comic').img['src'])
        self.bot.logger.info(img)
        em = dmbd.newembed(ctx.author, 'Cyanide and Happiness RCG', u=img)
        em.set_image(url=img)
        await ctx.send(embed=em)
        await self.bot.cogs['Wordcount'].cmdcount('cyanidercg')


def setup(bot):
    bot.add_cog(Comics(bot))
