
import asyncio
import logging
import random

from typing import List, Optional

import rapidjson

from bs4 import BeautifulSoup
from discord.ext import commands

from utility import discordembed as dmbd
from main import MyClient


log = logging.getLogger(__name__)


class Comics(commands.Cog):

    def __init__(self, bot: MyClient):
        self.bot = bot
        self.bot.loop.create_task(self.refreshxkcd())
        self.bot.loop.create_task(self.refreshcyanide())
        self.dead_cyanide: List[int] = []

    async def refreshxkcd(self) -> None:
        while True:
            log.info('Refreshing XKCD Comics.')
            async with self.bot.session.get("http://xkcd.com/info.0.json") as r:
                if r.status != 200:
                    log.warning("XKCD is down. Trying again in 1 minute.")
                    await asyncio.sleep(60)
                    continue
                j = await r.json()
                self.highest_xkcd = j['num']
            await asyncio.sleep(3600)

    async def getxkcd(self, num: int) -> Optional[dict]:
        """ Num should be passed as an INT """
        with await self.bot.db.redis as redis:
            result = await redis.hget('xkcd', num)
            if result is None:
                async with self.bot.session.get(f"http://xkcd.com/{num}/info.0.json") as r:
                    if r.status != 200:
                        log.error(f"Unable to get XKCD #{num}")
                        return {}
                    j = await r.json()
                await redis.hmset_dict('xkcd', {num: rapidjson.dumps(j)})
                return j
        return rapidjson.loads(result.decode('utf-8'))

    @commands.command()
    async def xkcd(self, ctx: commands.Context) -> None:
        """Gives a random XKCD Comic"""
        number = random.randint(1, self.highest_xkcd)
        result = await self.getxkcd(number)
        if not result:
            return

        em = dmbd.newembed(ctx.author, result['safe_title'], u=f"http://xkcd.com/{number}")
        em.set_image(url=result['img'])
        em.add_field(
            name=result['alt'],
            value="{month}/{day}/{year}".format_map(result))
        await ctx.send(embed=em)

    async def refreshcyanide(self) -> None:
        while True:
            log.info('Refreshing C&H Comics.')
            async with self.bot.session.get("http://explosm.net/comics/latest") as r:
                if r.status != 200:
                    log.warning("Cyanide&Happiness is down")
                    await asyncio.sleep(60)
                    continue
                soup = BeautifulSoup(await r.text(), 'html.parser')
            self.cyanidemax = int(soup.find(property='og:url').get('content').split('/')[-2])
            await asyncio.sleep(3600)

    async def getcyanide(self, num: int) -> Optional[str]:
        with await self.bot.db.redis as redis:
            result = await redis.hget('cyanide', num)
            if result is None:
                async with self.bot.session.get(f'http://explosm.net/comics/{num}') as r:
                    if r.status != 200:
                        log.warning(f"Unable to get Cyanide #{num}")
                        return None
                    soup = BeautifulSoup(await r.text(), 'html.parser')
                if soup.prettify().startswith('Could not'):
                    self.dead_cyanide.append(num)
                    return None
                img = f'http:{soup.find(id="main-comic")["src"]}'
                await redis.hmset_dict('xkcd', {num: img})
                return img
    
        return result.decode('utf-8')

    @commands.command()
    async def cyanide(self, ctx: commands.Context) -> None:
        """ Gives a random Cyanide & Happiness Comic"""
        img = None
        while img is None:
            number = random.randint(39, self.cyanidemax)
            if number in self.dead_cyanide:
                continue
            img = await self.getcyanide(number)
        # whatever reason, comics 1 - 38 don't exist.
        em = dmbd.newembed(ctx.author, 'Cyanide and Happiness', str(number), u=f'http://explosm.net/comics/{number}')
        em.set_image(url=img)
        await ctx.send(embed=em)

    @commands.command()
    async def cyanidercg(self, ctx: commands.Context) -> None:
        """ Gives a randomly generated Cyanide & Happiness Comic"""
        async with self.bot.session.get('http://explosm.net/rcg') as r:
            if r.status != 200:
                log.warning("Unable to get RCG for Cyanide")
                await ctx.send('Could not get you a random Cyanide&Happiness at this time.')
                return
            soup = BeautifulSoup(await r.text(), 'html.parser')
        img = f"http:{soup.find(id='rcg-comic').img['src']}"
        em = dmbd.newembed(ctx.author, 'Cyanide and Happiness RCG', u=img)
        em.set_image(url=img)
        await ctx.send(embed=em)


def setup(bot: MyClient) -> None:
    bot.add_cog(Comics(bot))
