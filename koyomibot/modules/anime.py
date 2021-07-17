""" To Get an Anime or Manga from MyAnimeList"""
import logging
from typing import Optional

from discord.ext import commands

import koyomibot.utility.discordembed as dmbd
from koyomibot.main import MyClient

log = logging.getLogger(__name__)


class Anime(commands.Cog):
    """Searches up stuff on My Anime List"""

    search_jikan = "https://api.jikan.moe/v3/search/{}/?q={}&limit=10"
    get_jikan = "https://api.jikan.moe/v3/{}/{}"
    priority_types = ("TV", "Movie")

    def __init__(self, bot: MyClient):
        self.bot = bot

    async def get_anime(self, string: str) -> Optional[dict]:
        cache_string = f"animesearch:{string}"

        # TODO: Refactoring this out...
        mal_id = await self.bot.db.redis.get(cache_string)
        if mal_id is None:
            url = self.search_jikan.format("anime", string)
            async with self.bot.session.get(url) as r:
                if r.status != 200:
                    log.error(f"Status: {r.status}. Did not get INFO from {url}")
                    return None
                results = await r.json()
            if not results["results"]:
                return {}
            # Iterate through the list to find the first "TV" or "MOVIE"
            for ani in results["results"]:
                if ani["type"] in self.priority_types:
                    result = ani
                    break
            else:
                result = results["results"][0]
            mal_id = result["mal_id"]
            await self.bot.db.redis.set(cache_string, int(mal_id))

        # Now get the actual anime details:
        cache_string = f"anime:{mal_id}"
        return await self.bot.request_get(self.get_jikan.format("anime", mal_id), cache_str=cache_string)

    @commands.command()
    async def animetrailer(self, ctx: commands.Context, *, anime_search: str) -> None:
        if len(anime_search) < 3:
            return
        result = await self.get_anime(anime_search)
        if result is None:
            return

        trailer_url = result.get("trailer_url")
        if not trailer_url:
            return
        trailer_url = f"https://youtu.be/{trailer_url.split('/')[-1].split('?')[0]}"
        await ctx.send(trailer_url)

    @commands.command()
    async def anime(self, ctx: commands.Context, *, anime_search: str) -> None:
        if len(anime_search) < 3:
            return
        result = await self.get_anime(anime_search)
        if result is None:
            return

        em = dmbd.newembed(
            a=ctx.author,
            t=result["title"],
            d=result["title_japanese"],
            u=result["url"],
            footer="Jikan & MAL",
        )
        em.set_image(url=result["image_url"])
        em.add_field(name="Score", value=result["score"])
        em.add_field(name="Rank", value=result["rank"])
        em.add_field(name="Popularity", value=result["popularity"])
        em.add_field(name="Type", value=result["type"])
        em.add_field(name="Episodes", value=result["episodes"])
        em.add_field(name="Status", value=result["status"])
        em.add_field(name="Genre", value=", ".join(res["name"] for res in result["genres"]))
        em.add_field(name="Synopsis", value=result["synopsis"])
        await ctx.send(embed=em)

    async def get_manga(self, string: str) -> Optional[dict]:
        cache_string = f"mangasearch:{string}"
        mal_id = await self.bot.db.redis.get(cache_string, encoding="utf-8")
        if mal_id is None:
            url = self.search_jikan.format("manga", string)
            async with self.bot.session.get(url) as r:
                if r.status != 200:
                    log.error(f"Status: {r.status}. Did not get INFO from {url}")
                    return None
                results = await r.json()
            if not results["results"]:
                return {}
            result = results["results"][0]
            mal_id = result["mal_id"]
            await self.bot.db.redis.set(cache_string, int(mal_id))

        # Now get the actual manga details:
        cache_string = f"manga:{mal_id}"
        return await self.bot.request_get(self.get_jikan.format("manga", mal_id), cache_str=cache_string)

    @commands.command()
    async def manga(self, ctx: commands.Context, *, manga_search: str) -> None:
        if len(manga_search) < 3:
            return
        result = await self.get_manga(manga_search)
        if result is None:
            return

        em = dmbd.newembed(
            a=ctx.author,
            t=result["title"],
            d=result["title_japanese"],
            u=result["url"],
            footer="Jikan & MAL",
        )
        em.set_image(url=result["image_url"])
        em.add_field(name="Score", value=result["score"])
        em.add_field(name="Rank", value=result["rank"])
        em.add_field(name="Popularity", value=result["popularity"])
        em.add_field(name="Type", value=result["type"])
        em.add_field(name="Volumes/Chapters", value=f"{result['volumes']}/{result['chapters']}")
        em.add_field(name="Status", value=result["status"])
        em.add_field(name="Genre", value=", ".join(res["name"] for res in result["genres"]))
        em.add_field(name="Synopsis", value=result["synopsis"])
        await ctx.send(embed=em)


def setup(bot):
    """Setup Anime.py"""
    bot.add_cog(Anime(bot))
