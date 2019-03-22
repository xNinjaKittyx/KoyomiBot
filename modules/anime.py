""" To Get an Anime or Manga from MyAnimeList"""
import logging
from datetime import datetime

import rapidjson
from bs4 import BeautifulSoup
from discord.ext import commands

import utility.discordembed as dmbd


class Anime:
    """Searches up stuff on My Anime List"""

    @staticmethod
    def getlink(series_id, series_type):
        """Getter Function for Anime or Manga Link from MAL"""
        return f"https://anilist.co/{series_type}/{series_id}"

    async def getaccesstoken(self):
        async with self.bot.session.post(
            'https://anilist.co/api/auth/access_token', data={
                'grant_type': 'client_credentials',
                'client_id': self.bot.config['AnilistID'],
                'client_secret': self.bot.config['AnilistSecret']
            }
        ) as r:
            if r.status == 200:
                results = await r.json(loads=rapidjson.loads)
                self.access_token = results['access_token']
                self.lastaccess = datetime.today()
            else:
                self.bot.logger.warning("Cannot get Anilist Access Token")
                return

    def __init__(self, bot):
        self.bot = bot
        if not self.bot.config['AnilistSecret'] or not self.bot.config['AnilistID']:
            self.bot.logger.warning('ID or Secret is missing for AniList')
            raise ImportError
        self.access_token = None
        self.lastaccess = None
        self.firsttime = True

    def getinfo(self, author, series):
        """ Get the Info Message of the MalLink Class. Returns with Embed"""

        em = dmbd.newembed(
            author,
            series['title_japanese'],
            series['title_romaji'],
            self.getlink(series['id'], series['series_type'])
        )
        em.set_thumbnail(url="https://anilist.co/img/logo_al.png")
        em.set_image(url=series['image_url_med'])
        if series['series_type'] == 'anime':  # if anime
            em.add_field(name="Episodes", value=series['total_episodes'])
            try:
                em.add_field(name="Length", value=str(series['duration']) + " minutes")
            except KeyError:
                pass
            try:
                em.add_field(name="Status", value=series['airing_status'])
            except KeyError:
                pass

        elif series['series_type'] == 'manga':  # if manga
            em.add_field(name="Chapters", value=series['total_chapters'])
            em.add_field(name="Volumes", value=series['total_volumes'])
            try:
                em.add_field(name="Status", value=series['publishing_status'])
            except KeyError:
                pass

        em.add_field(name="Score", value=series['average_score'])
        em.add_field(name="Type", value=series['type'])
        if series.get('description', None):
            cleantext = BeautifulSoup(series['description'], "html.parser").text[:500] + "..."
            em.add_field(name="Synopsis", value=cleantext)
        return em

    async def refreshtoken(self):
        if self.firsttime:
            self.firsttime = False
            await self.getaccesstoken()
        delta = (datetime.today() - self.lastaccess)
        if delta.seconds > 3600 or delta.days > 0:
            await self.getaccesstoken()

    @commands.command()
    async def anime(self, ctx, *, ani: str):
        """ Returns the top anime of whatever the user asked for."""
        await self.refreshtoken()

        url = f'https://anilist.co/api/anime/search/{ani}?access_token={self.access_token}'

        async with self.bot.session.get(url) as r:
            if r.status == 200:
                animelist = await r.json(loads=rapidjson.loads)
                try:
                    await ctx.send(animelist["error"]["message"][0])
                except Exception as e:
                    logging.error(f'Anime returned {e}')
                    pass

                chosen = {}
                for x in animelist:
                    if x['title_romaji'].lower() == ani.lower():
                        chosen = x
                        break
                    elif x['title_english'].lower() == ani.lower():
                        chosen = x
                        break
                if chosen == {}:
                    for x in animelist:
                        if x['type'] == "TV":
                            chosen = x
                            break
                    if chosen == {}:
                        for x in animelist:
                            if x['type'] == "Movie":
                                chosen = x
                                break
                        if chosen == {}:
                            chosen = animelist[0]
                await ctx.send(embed=self.getinfo(ctx.author, chosen))
            else:
                self.bot.logger.warning("No 200 status from Anime")
        await self.bot.cogs['Wordcount'].cmdcount('anime')

    @commands.command()
    async def manga(self, ctx, *, mang: str):
        """ Returns the top manga of whatever the user asked for."""

        await self.refreshtoken()
        url = f'https://anilist.co/api/manga/search/{mang}?access_token={self.access_token}'

        async with self.bot.session.get(url) as r:
            if r.status == 200:
                mangalist = await r.json(loads=rapidjson.loads)
                if 'error' in mangalist:
                    await ctx.send(mangalist["error"]["message"][0])
                    return
                chosen = {}
                for x in mangalist:
                    if x['title_romaji'].lower() == mang.lower():
                        chosen = x
                        break
                    elif x['title_english'].lower() == mang.lower():
                        chosen = x
                        break
                if chosen == {}:
                    for x in mangalist:
                        if x['type'] == "Manga" or x['type'] == "Novel":
                            chosen = x
                            break
                    if chosen == {}:
                        for x in mangalist:
                            if x['type'] == "Manhua" or x['type'] == "Manhwa":
                                chosen = x
                                break
                        if chosen == {}:
                            chosen = mangalist[0]
                await ctx.send(embed=self.getinfo(ctx.author, chosen))
            else:
                self.bot.logger.warning("No 200 status from Manga")
        await self.bot.cogs['Wordcount'].cmdcount('anime')


def setup(bot):
    """Setup Anime.py"""
    bot.add_cog(Anime(bot))
