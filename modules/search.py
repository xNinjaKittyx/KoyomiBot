import logging

from typing import Callable

import discord
import wikipedia
import xmltodict
from discord.ext import commands

import utility.discordembed as dmbd
from main import MyClient


log = logging.getLogger(__name__)


def get_check(msg: discord.Message) -> Callable:
    def check(reaction: discord.Reaction, user: discord.User) -> bool:
        if user.bot:
            return False
        return str(reaction.emoji) in ["◀", "▶", "❌"] and reaction.message.id == msg.id

    return check


class Search(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot

    async def get_page(self, check: Callable, msg: discord.Message, page: int, max_page: int) -> int:
        try:
            res, user = await self.bot.wait_for("reaction_add", check=check, timeout=300,)
        except TimeoutError:
            await msg.clear_reactions()
            return -1
        if res is None:
            await msg.clear_reactions()
            return -1
        elif res.emoji == "❌":
            await msg.clear_reactions()
            return -1
        elif res.emoji == "◀":
            await msg.remove_reaction(res.emoji, user)
            if page > 0:
                return page - 1
        elif res.emoji == "▶":
            await msg.remove_reaction(res.emoji, user)
            if page < max_page:
                return page + 1
        return page

    @commands.command()
    async def safebooru(self, ctx: commands.Context, *, search: str) -> None:
        """Searches Safebooru"""
        link = f"https://safebooru.org/index.php?page=dapi&s=post&q=index&limit=20&tags={search.replace(' ', '_')}"

        async with self.bot.session.get(link) as r:
            if r.status != 200:
                log.error("Safebooru search failed")
                return
            try:
                weeblist = xmltodict.parse(await r.text())["posts"]["post"]
            except KeyError:
                weeblist = []
        if not isinstance(weeblist, list):
            size = 1
        else:
            size = len(weeblist)
        page = 0
        max_page = size - 1

        title = f"Safebooru: {search}"
        sample_url = "{0[@sample_url]}"
        file_url = "{0[@file_url]}"
        desc = "{0} / " + str(size)
        source = "[Here]({0[@source]})"
        em = dmbd.newembed(ctx.author, title)
        if size == 0:
            em.description = f"No Results Found For {search}"
            await ctx.send(embed=em)
            return
        elif size == 1:
            em.set_image(url=sample_url.format(weeblist))
            em.url = file_url.format(weeblist)
            em.description = desc.format(page + 1)
            em.add_field(name="Source", value=source.format(weeblist))
            em.add_field(name="Tags", value=weeblist["@tags"])
            print(em.to_dict())
            await ctx.send(embed=em)
        else:
            em.set_image(url=sample_url.format(weeblist[0]))
            em.url = file_url.format(weeblist[0])
            em.description = desc.format(1)
            em.add_field(name="Source", value=source.format(weeblist[0]))
            em.add_field(name="Tags", value=weeblist[0]["@tags"])
            msg = await ctx.send(embed=em)
            await msg.add_reaction("◀")
            await msg.add_reaction("▶")
            await msg.add_reaction("❌")

            check = get_check(msg)

            while True:
                page = await self.get_page(check, msg, page, max_page)
                if page == -1:
                    return

                em.set_image(url=sample_url.format(weeblist[page]))
                em.url = file_url.format(weeblist[page])
                em.description = desc.format(page + 1)
                em.clear_fields()
                em.add_field(name="Source", value=source.format(weeblist[page]))
                em.add_field(name="Tags", value=weeblist[page]["@tags"])
                await msg.edit(embed=em)

    async def parse_urban_def(self, ctx: commands.Context, definition: dict) -> discord.Embed:
        title = definition["word"]
        url = definition["permalink"]
        define = definition["definition"][:2048]
        thumbs_up = definition["thumbs_up"]
        thumbs_down = definition["thumbs_down"]
        example = definition["example"]
        author = definition["author"]
        desc = f"Defined by: {author}\n{define}\n\nExample: {example}\n\n👍{thumbs_up}\t👎{thumbs_down}"
        return dmbd.newembed(ctx.author, t=title, d=desc, u=url, footer="urbandictionary")

    @commands.command()
    async def urban(self, ctx: commands.Context, *, search: str) -> None:
        """ Searches Urban Dictionary. """
        async with self.bot.session.get(f"https://api.urbandictionary.com/v0/define?term={search}") as r:
            if r.status != 200:
                log.error(f"Urbandictionary Failed: {r.text}")
                return
            results = await r.json()

        size = len(results["list"])
        if size == 0:
            return
        elif size > 0:
            page = 0
            max_page = size - 1
            definition = results["list"][page]
            em = await self.parse_urban_def(ctx, definition)
            msg = await ctx.send(embed=em)

            if size > 1:
                await msg.add_reaction("◀")
                await msg.add_reaction("▶")
                await msg.add_reaction("❌")

                check = get_check(msg)

                while True:
                    page = await self.get_page(check, msg, page, max_page)
                    if page == -1:
                        return

                    definition = results["list"][page]
                    em = await self.parse_urban_def(ctx, definition)
                    await msg.edit(embed=em)

    @commands.command()
    async def wiki(self, ctx: commands.Context, *, search: str) -> None:
        """ Grabs Wikipedia Article """
        searchlist = wikipedia.search(search)
        if len(searchlist) < 1:
            title = "Searched for: " + search
            desc = "No Results Found"
            em = dmbd.newembed(ctx.author, title, desc)
            await ctx.send(embed=em)
        else:
            page = wikipedia.page(searchlist[0])

            title = page.title
            desc = wikipedia.summary(searchlist[0], 3)
            url = page.url
            em = dmbd.newembed(ctx.author, title, desc, url)

            em.set_image(url=page.images[0])
            em.set_thumbnail(
                url=(
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/"
                    "Wikipedia-logo-v2-en.svg/250px-Wikipedia-logo-v2-en.svg.png"
                )
            )
            await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Search(bot))
