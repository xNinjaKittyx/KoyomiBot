import logging

import orjson as json
from discord.ext import commands

import utility.discordembed as dmbd
from main import MyClient


log = logging.getLogger(__name__)


class Forex(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot

    @commands.command()
    async def forex(self, ctx: commands.Context, *args: str) -> None:
        num_of_args = len(args)
        if num_of_args == 1:
            base = "USD"
            if len(args[0]) != 3:
                return
            conversion = args[0].upper()
        elif num_of_args == 2:
            if len(args[0]) != 3 or len(args[1]) != 3:
                return
            base = args[0].upper()
            conversion = args[1].upper()
        else:
            return

        cache = await self.bot.db.redis.get(f"exchangerateapi:{base}")
        if cache is None:
            url = f"https://api.exchangeratesapi.io/latest?base={base}"
            async with self.bot.session.get(url) as r:
                if r.status != 200:
                    log.error("Could not get info from ExchangeRagesAPI")
                    return
                result = await r.json()
            await self.bot.db.redis.set(f"exchangerateapi:{base}", json.dumps(result))
        else:
            result = json.loads(cache)

        desc = f"{base} to {conversion} conversion"
        em = dmbd.newembed(ctx.author, "Foreign Exchange", desc, "https://exchangeratesapi.io/")
        em.add_field(name=f"1 {base}", value=f"{result['rates'][conversion]}  {conversion}")
        await ctx.send(embed=em)


def setup(bot: MyClient) -> None:
    """ Setup Forex Module"""
    bot.add_cog(Forex(bot))
