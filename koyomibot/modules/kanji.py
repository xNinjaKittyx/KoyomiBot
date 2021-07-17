import logging
import random

import discord
from discord.ext import commands

import koyomibot.utility.discordembed as dmbd
from koyomibot.main import MyClient
from koyomibot.utility.reactions import get_check, get_page_check

log = logging.getLogger(__name__)


class Kanji(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot

    async def _make_call(self, endpoint: str) -> int:
        if len(endpoint.split("/")) != 2:
            return None
        return await self.bot.request_get(f"https://kanjiapi.dev/v1/{endpoint}", cache_str=endpoint.replace("/", ":"))

    def _parse_kanji(self, ctx: commands.Context, result: dict) -> discord.Embed:

        em = dmbd.newembed(ctx.author, result["kanji"], d=result["heisig_en"])
        em.add_field(name="grade", value=result["grade"])
        em.add_field(name="meanings", value=",".join(result["meanings"]))
        if result["kun_readings"]:
            em.add_field(name="kun readings", value=",".join(result["kun_readings"]))
        if result["on_readings"]:
            em.add_field(name="on readings", value=",".join(result["on_readings"]))
        if result["name_readings"]:
            em.add_field(name="name readings", value=",".join(result["name_readings"]))

        return em

    @commands.command()
    async def kanji(self, ctx: commands.Context, *, character: str) -> bool:
        """Information about a Kanji character"""

        result = await self._make_call(f"kanji/{character}")
        if result is None:
            return False

        em = self._parse_kanji(ctx, result)
        await ctx.send(embed=em)
        return True

    def _kanji_fields(self, result: dict, embed: discord.Embed) -> None:
        embed.clear_fields()
        embed.description = ", ".join(result["meanings"][0]["glosses"])
        for variant in result["variants"]:
            embed.add_field(name=variant["written"], value=variant["pronounced"])

    @commands.command()
    async def kanjiwords(self, ctx: commands.Context, *, character: str):
        """Word Examples for a Kanji"""

        result = await self._make_call(f"words/{character}")
        if result is None:
            return False
        page = 0
        max_page = len(result)
        em = dmbd.newembed(ctx.author, character)
        self._kanji_fields(result[page], em)
        msg = await ctx.send(embed=em)
        if max_page == 1:
            return
        await msg.add_reaction("◀")
        await msg.add_reaction("▶")
        await msg.add_reaction("❌")
        check = get_page_check(msg)
        while True:
            try:
                res, user = await self.bot.wait_for("reaction_add", check=check, timeout=120)
            except TimeoutError:
                await msg.clear_reactions()
                break
            if res is None:
                await msg.clear_reactions()
                break
            elif res.emoji == "❌":
                await msg.clear_reactions()
                break
            elif res.emoji == "◀":
                await msg.remove_reaction(res.emoji, user)
                page = max(0, page - 1)
            elif res.emoji == "▶":
                await msg.remove_reaction(res.emoji, user)
                page = min(max_page, page + 1)
            self._kanji_fields(result[page], em)
            await msg.edit(embed=em)

        return True

    @commands.command()
    async def kanjireading(self, ctx: commands.Context, *, characters: str):
        """Possible Kanji for a given reading"""

        result = await self._make_call(f"reading/{characters}")
        if result is None:
            return False
        em = dmbd.newembed(ctx.author, characters)
        em.add_field(name="Main Kanji", value=",".join(result["main_kanji"]))
        em.add_field(name="Name Kanji", value=",".join(result["name_kanji"]))
        await ctx.send(embed=em)
        return True

    @commands.command()
    async def kanjitest(self, ctx: commands.Context, *, difficulty: int) -> bool:
        """Test your kanji skills difficulty 1-4"""
        if difficulty not in range(5):
            return False
        endpoint = f"kanji/{('joyo', 'jouyou', 'jinmeiyo', 'jinmeiyou')[difficulty - 1]}"

        result = await self._make_call(endpoint)
        if result is None:
            return False

        # Get random Kanji
        kanji = random.choice(result)
        result = await self._make_call(f"kanji/{kanji}")
        if result is None:
            return False

        em = dmbd.newembed(ctx.author, kanji, d=f"|| {result['heisig_en']} ||")

        message = await ctx.send(embed=em)
        await message.add_reaction("✅")

        # TODO: Add additional info if wanted
        check = get_check(message)

        try:
            res, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)
        except TimeoutError:
            pass
        em = self._parse_kanji(ctx, result)
        await message.edit(embed=em)
        return True


def setup(bot: MyClient) -> None:
    bot.add_cog(Kanji(bot))
