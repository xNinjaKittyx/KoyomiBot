
import random

import aiohttp
from discord.ext import commands
import wikipedia
import xmltodict

import utility.discordembed as dmbd

class Search:

    def __init__(self, bot):
        self.bot = bot

    async def gfylink(self, keyword, count, author):
        link = "https://api.gfycat.com/v1test/gfycats/search?search_text=" + str(keyword) + "&count=" + str(count)

        async with self.bot.session.get(link) as r:
            if r.status != 200:
                self.bot.cogs['Log'].output('Gyfcat returned ' + r.status)
            giflist = await r.json()
            num = random.randint(0, count-1)
            gif = giflist["gfycats"][num]
            title = gif["gfyName"]
            desc = gif["title"]
            if gif["tags"] != None:
                desc += " #" + " #".join([x for x in gif["tags"]])

            url = "https://gfycat.com/" + title
            return dmbd.newembed(author, title, desc, url)

    @commands.command(pass_context=True)
    async def owgif(self, ctx):
        """Random Overwatch Gyfcat"""
        em = await self.gfylink("overwatch", 100, ctx.message.author)
        await self.bot.say(embed=em)
        await self.bot.say(em.url)
        self.bot.cogs['Wordcount'].cmdcount('owgif')

    @commands.command(pass_context=True)
    async def gfy(self, ctx, *, keyword: str):
        """Does a search on gyfcat"""
        em = await self.gfylink(keyword, 50, ctx.message.author)
        await self.bot.say(embed=em)
        await self.bot.say(em.url)
        self.bot.cogs['Wordcount'].cmdcount('gfy')

    @commands.command(pass_context=True, no_pm=True)
    async def safebooru(self, ctx, *, search: str):
        """Searches Safebooru"""
        link = ("http://safebooru.org/index.php?page=dapi&s=post&q=index" +
                "&tags=" + search.replace(' ', '_'))

        async with self.bot.session.get(link) as r:
            if r.status != 200:
                self.bot.cogs['Log'].output('Safebooru failed')
            weeblist = xmltodict.parse(await r.text())

        numOfResults = int(weeblist['posts']['@count'])

        # Find how many pages there are

        numOfPages = int(numOfResults / 100)
        remaining = numOfResults % 100

        author = ctx.message.author
        title = 'Safebooru'
        desc = 'Searched For ' + search
        em = dmbd.newembed(author, title, desc)

        if numOfResults == 0:
            em.description = "No Results Found For " + search
        elif numOfResults == 1:
            em.set_image(url='https:' + str(weeblist['posts']['post']['@file_url']))
        else:
            if numOfPages == 0:
                chosenone = random.randint(0, min(99, numOfResults-1))
                em.set_image(url='https:' + str(weeblist['posts']['post'][chosenone]['@file_url']))
            else:
                page = random.randint(0, numOfPages)
                # Avoiding oversearching, and cutting the page limit to 3.
                # Sometimes really unrelated stuff gets put in.
                async with self.bot.session.get(link + '&pid=' + str(min(3, page))) as r:
                    if r.status != 200:
                        return
                    weeblist = xmltodict.parse(await r.text())

                if page == numOfPages:
                    chosenone = random.randint(0, min(99, remaining))
                    em.set_image(url='https:' + str(weeblist['posts']['post'][chosenone]['@file_url']))
                else:
                    chosenone = random.randint(0, 99)
                    em.set_image(url='https:' + str(weeblist['posts']['post'][chosenone]['@file_url']))

            self.bot.cogs['Wordcount'].cmdcount('safebooru')
        await self.bot.say(embed=em)

    @commands.command(pass_context=True)
    async def wiki(self, ctx, *, search: str):
        """ Grabs Wikipedia Article """
        searchlist = wikipedia.search(search)
        if len(searchlist) < 1:
            author = ctx.message.author
            title = "Searched for: " + search
            desc = 'No Results Found'
            em = dmbd.newembed(author, title, desc)
            await self.bot.say(embed=em)
        else:
            page = wikipedia.page(searchlist[0])

            author = ctx.message.author
            title = page.title
            desc = wikipedia.summary(searchlist[0], 3)
            url = page.url
            em = dmbd.newembed(author, title, desc, url)

            em.set_image(url=page.images[0])
            em.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Wikipedia-logo-v2-en.svg/250px-Wikipedia-logo-v2-en.svg.png")
            self.bot.cogs['Wordcount'].cmdcount('wiki')
            await self.bot.say(embed=em)

def setup(bot):
    bot.add_cog(Search(bot))
