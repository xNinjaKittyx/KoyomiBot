import functools
import io
import logging
import os
from datetime import date, timedelta

import discord
import matplotlib.pyplot as plt
import pandas as pd
from discord.ext import commands
from iexfinance.stocks import Stock, get_historical_data

from koyomibot.utility import discordembed as dmbd

log = logging.getLogger(__name__)


def human_format(num):
    num = float(f"{num:.3g}")
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return "{}{}".format(f"{num:f}".rstrip("0").rstrip("."), ["", "K", "M", "B", "T"][magnitude])


class Stocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.environ["IEX_TOKEN"] = self.bot.key_config.IEX_TOKEN
        os.environ["IEX_API_VERSION"] = self.bot.key_config.IEX_API_VERSION

    async def _get_historical_data(self, ticker):
        end = date.today()
        start = end - timedelta(days=28)
        df = await self.bot.db.get_dataframe(f"ticker{ticker}")
        if df is None:
            df = await self.bot.loop.run_in_executor(
                None, functools.partial(get_historical_data, ticker, start, end, output_format="pandas")
            )
            await self.bot.db.set_dataframe(f"ticker{ticker}", df)
        return df

    async def _get_quote(self, ticker):
        return (await self.bot.loop.run_in_executor(None, functools.partial(Stock(ticker).get_quote))).head(1)

    @commands.command()
    async def quote(self, ctx, *, ticker: str):
        """ Basic Quote """
        ticker = ticker.upper()
        df = await self._get_historical_data(ticker)
        if df.empty:
            await ctx.send(f"Could not find data for {ticker}")
            return

        plt.style.use("Solarize_Light2")

        df.index = pd.DatetimeIndex(df.index)
        df.plot(
            y=["close", "open"], ylabel="US Dollars", title=ticker, lw=1,
        )
        today_data = await self._get_quote(ticker)
        log.info(today_data)

        image_buffer = io.BytesIO()
        plt.savefig(image_buffer, format="png")
        image_buffer.seek(0)

        discord_file = discord.File(image_buffer, filename=f"{ticker}.png")

        embed = dmbd.newembed(ctx.author, ticker, today_data["companyName"].values[0])
        embed.set_image(url=f"attachment://{ticker}.png")

        embed.add_field(name="Open", value=today_data["iexOpen"].values[0])
        embed.add_field(name="Close", value=today_data["iexClose"].values[0])
        embed.add_field(name="% Change Today", value=f"{today_data['changePercent'].values[0] * 100:.3f}%")
        embed.add_field(name="Volume", value=today_data["iexVolume"].values[0])
        embed.add_field(name="Latest Price", value=today_data["latestPrice"].values[0])
        embed.add_field(name="52 Week High", value=today_data["week52High"].values[0])
        embed.add_field(name="52 Week Low", value=today_data["week52Low"].values[0])
        embed.add_field(name="Market Cap", value=human_format(today_data["marketCap"].values[0]))
        await ctx.send(file=discord_file, embed=embed)


def setup(bot):
    bot.add_cog(Stocks(bot))
