import asyncio
import logging
from datetime import datetime

from discord.ext import commands

from koyomibot.utility import discordembed as dmbd

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

    def create_weather_task(self, guild, zip_code, voice_channel):
        async def task():
            while True:
                try:
                    async with self.bot.session.get(
                        f"{self.weather_url}?zip={zip_code},US&units=imperial"
                        f"&appid={self.bot.key_config.OpenWeatherAPIToken}"
                    ) as req:
                        if req.status != 200:
                            log.error(f"OWA API failed: {req.content}")
                            return
                        result = await req.json()

                        icon = int(result["weather"][0]["icon"][:2])

                        icons = ["", "☼", "🌤", "🌥", "", "", "", "", "", "🌧", "🌧", "🌩", "", "⛄"]
                        if icon == 50:
                            real_icon = "🌫"
                        else:
                            real_icon = icons[icon]

                        weather_result = (
                            f"{real_icon} | {result['main']['temp']}°F | {result['main']['humidity']}% | "
                            f"{result['weather'][0]['description'].capitalize()}"
                        )

                        await voice_channel.edit(name=weather_result)

                        self._weather_info[guild.id] = {
                            "last_execution": datetime.now().isoformat(),
                            "result": weather_result,
                        }
                except Exception:
                    log.exception(f"{guild.id} - {zip_code} - {voice_channel.id}")

                # Sleep 1 Hour
                await asyncio.sleep(3600)

        return task()

    @commands.command()
    async def weather_register(self, ctx: commands.Context, zip_code: str, channel_id: str):
        # Register weather to a Voice Channel
        try:
            voice_channel = await self.bot.fetch_channel(channel_id)

            if ctx.guild.id in self._weather_tasks:
                await ctx.send("Weather Task already exists. Use weather_unregister before using this again.")
                return

            task = self.create_weather_task(ctx.guild, zip_code, voice_channel)

            if task is None:
                raise Exception("Guild already has a task.")
            self._weather_tasks[ctx.guild.id] = asyncio.ensure_future(task)

            await ctx.send("Registration Complete.")
        except Exception:
            log.exception("Registration Failed")
            await ctx.send("Registration Failed")

    @commands.command()
    async def weather_unregister(self, ctx: commands.Context):

        self._weather_tasks[ctx.guild.id].cancel()
        del self._weather_tasks[ctx.guild.id]

    @commands.command()
    async def weather_debug_stats(self, ctx: commands.Context):
        if ctx.author.id != 82221891191844864:
            return

        log.info(self._weather_tasks)
        log.info(self._weather_info)

    @commands.command()
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

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Weather(bot))
