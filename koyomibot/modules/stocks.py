import io
import logging
import os
from datetime import date, timedelta

import discord
import matplotlib.pyplot as plt
import pandas as pd
from discord.ext import commands
from iexfinance.stocks import get_historical_data

from koyomibot.utility import discordembed as dmbd

log = logging.getLogger(__name__)


class Stocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.environ["IEX_TOKEN"] = self.bot.key_config.IEX_TOKEN
        os.environ["IEX_API_VERSION"] = self.bot.key_config.IEX_API_VERSION

    @commands.command()
    async def quote(self, ctx, *, ticker: str):
        """ Basic Quote """
        ticker = ticker.upper()
        end = date.today()
        start = end - timedelta(days=365)
        df = get_historical_data(ticker, start, end, output_format="pandas")
        if df.empty:
            await ctx.send(f"Could not find data for {ticker}")
            return

        plt.style.use("Solarize_Light2")

        df.index = pd.DatetimeIndex(df.index)
        df.plot(
            y=["close", "open"], ylabel="US Dollars", title=ticker, lw=1,
        )
        today_data = df.tail(1)

        image_buffer = io.BytesIO()
        plt.savefig(image_buffer, format="png")
        image_buffer.seek(0)

        discord_file = discord.File(image_buffer, filename=f"{ticker}.png")

        embed = dmbd.newembed(ctx.author, ticker, "Today's Quote")
        embed.set_image(url=f"attachment://{ticker}.png")
        for field in ("open", "close", "high", "low", "volume"):
            embed.add_field(name=field.capitalize(), value=today_data[field].values[0])
        embed.add_field(name="% Change Today", value=today_data["changePercent"].values[0])
        await ctx.send(file=discord_file, embed=embed)


def setup(bot):
    bot.add_cog(Stocks(bot))
