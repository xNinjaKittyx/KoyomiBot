import asyncio
import logging
import re

import bs4
import discord
from discord.ext import commands

import koyomibot.utility.discordembed as dmbd
from koyomibot.main import MyClient

log = logging.getLogger(__name__)


class Dragalia(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot
        self.api_link = "https://dragalialost.gamepedia.com/api.php?action=parse&format=json"
        self._data = {}
        self.bot.loop.create_task(self.update_values())

    async def _update_page_links(self, key: str, page: str):
        url = f"{self.api_link}&page={page}&prop=links"
        try:
            async with self.bot.session.get(url) as r:
                if r.status != 200:
                    log.warning(f"{url} returned {r.text}")
                    await asyncio.sleep(5)
                data = await r.json()
                self._data[key] = [d["*"] for d in data["parse"]["links"]]
        except Exception as e:
            log.exception(f"Dragalia fetch failed for {key}: {e}")

    async def update_values(self) -> None:
        while True:
            # Grabbing the List of Adventurers.
            await self._update_page_links("adventurer", "Adventurer_Grid")
            await self._update_page_links("dragon", "Dragon_Grid")
            await self._update_page_links("wyrmprint", "Wyrmprint_Grid")
            await self._update_page_links("weapon", "Weapon_Grid")

            await asyncio.sleep(3600)

    @commands.group()
    async def dragalia(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            # TODO: Display Help message?
            await ctx.send("This command has several subcommands. Try `dragalia help`")

    @dragalia.command()
    async def help(self, ctx: commands.Context) -> None:
        await ctx.send("Coming Soon...")

    def parse_adventurer(self, soup: bs4.BeautifulSoup, embed: discord.Embed):
        embed.set_image(url=soup.find(class_="adv-portrait").a.img["src"])
        embed.set_thumbnail(url=soup.find(string="Class").parent.parent.img["src"])
        embed.add_field(
            name="Rarity",
            value=":star: " * int(soup.find(string="Base Rarity").parent.parent.img["alt"][-5]),
            inline=False,
        )
        embed.add_field(
            name="Total Max HP",
            value=soup.find(string="Total Max HP").parent.parent.next_sibling.next_sibling.span.span.next_sibling,
        )
        embed.add_field(
            name="Total Max Str",
            value=soup.find(string="Total Max Str").parent.parent.next_sibling.next_sibling.span.span.next_sibling,
        )
        embed.add_field(
            name="Base Min Might",
            value=soup.find(string="Base Min Might").parent.next_sibling.next_sibling.span.span.next_sibling,
        )
        embed.add_field(
            name="Base Max Might",
            value=soup.find(string="Base Max Might").parent.next_sibling.next_sibling.span.span.next_sibling,
        )
        for value in (
            "Defense",
            "Gender",
            "Race",
            "Japanese Title",
            "Japanese Name",
            "Voice Actor (EN)",
            "Voice Actor (JP)",
            "Obtained From",
            "Release Date",
            "Availability",
        ):
            embed.add_field(
                name=value, value=soup.find(string=value).parent.parent.div.next_sibling.next_sibling.text.strip()
            )

    async def parse_input(self, ctx: commands.Context, content: str, content_type: str) -> None:
        if not content:
            await ctx.send(self._data[content_type])
            return None
        content = content.title()

        if content not in self._data[content_type]:
            await ctx.send(f"That {content_type} {content} does not exist in Dragalia.")
            return None

        url = f"{self.api_link}&page={content}&prop=text"
        async with self.bot.session.get(url) as req:
            if req.status != 200:
                log.warning(f"{url} returned {await req.text()}")
                return None
            data = (await req.json())["parse"]["text"]["*"]
            soup = bs4.BeautifulSoup(data, "html.parser")
        embed = dmbd.newembed(
            "Dragalia Lost",
            content,
            re.sub(r"\n+", "\n", soup.find(string="Description").parent.next_sibling.next_sibling.text),
            f"https://dragalialost.gamepedia.com/{content.replace(' ', '_')}",
        )
        if content_type == "adventurer":
            self.parse_adventurer(soup, embed)

        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send(embed.to_dict())

    @dragalia.command()
    async def adventurer(self, ctx: commands.Context, *, adventurer: str = "") -> None:
        await self.parse_input(ctx, adventurer, "adventurer")

    @dragalia.command()
    async def dragon(self, ctx: commands.Context, *, dragon: str = "") -> None:
        await self.parse_input(ctx, dragon, "dragon")

    @dragalia.command()
    async def wyrmprint(self, ctx: commands.Context, *, wyrmprint: str = "") -> None:
        await self.parse_input(ctx, wyrmprint, "wyrmprint")

    @dragalia.command()
    async def weapon(self, ctx: commands.Context, *, weapon: str = "") -> None:
        await self.parse_input(ctx, weapon, "weapon")

    @dragalia.command()
    async def optiwyrm(self, ctx: commands.Context) -> None:
        embed = dmbd.newembed("Dragalia Lost", "Wyrmprints",)
        embed.set_image(url="https://i.redd.it/2yn68xpaghq31.jpg")
        await ctx.send(embed=embed)


def setup(bot: discord.Client) -> None:
    bot.add_cog(Dragalia(bot))
