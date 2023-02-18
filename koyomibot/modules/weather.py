import logging

from discord.commands import slash_command
from discord.ext import commands

from koyomibot.utility import discordembed as dmbd
from koyomibot.utility.allowed_guilds import ALLOWED_GUILDS

log = logging.getLogger(__name__)


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.weather_url = "https://api.openweathermap.org/data/2.5/weather"

        self._weather_tasks = {}
        self._weather_info = {}

        self._guild_tasks = set()

        # On a fresh boot, need to recreate the weather tasks

    def cog_check(self, ctx: commands.Context) -> bool:
        return bool(self.bot.key_config.OpenWeatherAPIToken)

    @slash_command(guild_ids=ALLOWED_GUILDS)
    async def weather(self, ctx: commands.Context, zip_code_or_city: str) -> None:
        """Sorry US only for now."""

        em = dmbd.newembed(ctx.author, "Weather")

        if zip_code_or_city.isdigit():
            # Then this is a zip code
            async with self.bot.session.get(
                f"{self.weather_url}?zip={zip_code_or_city}&units=imperial&"
                f"appid={self.bot.key_config.OpenWeatherAPIToken}"
            ) as req:
                if req.status != 200:
                    log.error(f"OWA API failed: {req.content}")
                    return
                result = await req.json()
        else:
            # Use the regular API
            async with self.bot.session.get(
                f"{self.weather_url}?q={zip_code_or_city}&units=imperial&"
                f"appid={self.bot.key_config.OpenWeatherAPIToken}"
            ) as req:
                if req.status != 200:
                    log.error(f"OWA API failed: {req.content}")
                    return
                result = await req.json()

        em.description = f'{result["weather"][0]["description"].capitalize()} in {result["name"]}'

        em.add_field(name="Current", value=f'{result["main"]["temp"]}°F')
        em.add_field(name="Feels Like", value=f'{result["main"]["feels_like"]}°F')
        em.add_field(name="Humidity", value=result["main"]["humidity"])
        em.add_field(name="Pressure", value=result["main"]["pressure"])
        em.add_field(name="Wind", value=f'{result["wind"]["deg"]}° at {result["wind"]["speed"]} MPH')

        await ctx.respond(embed=em)


def setup(bot):
    bot.add_cog(Weather(bot))
