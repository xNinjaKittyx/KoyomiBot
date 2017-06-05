
# -*- coding: utf8 -*-
import random

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
                self.bot.cogs['Log'].output('[WARNING]: Safebooru Search Failed')
            weeblist = xmltodict.parse(await r.text())

        numOfResults = min(int(weeblist['posts']['@count']), 20)

        author = ctx.message.author
        title = 'Safebooru'
        desc = '1 / ' + str(numOfResults)
        em = dmbd.newembed(author, title, desc)
        if numOfResults == 0:
            em.description = "No Results Found For " + search
            await self.bot.say(embed=em)
            return
        elif numOfResults == 1:
            em.set_image(url='https:' + str(weeblist['posts']['post']['@file_url']))
            await self.bot.say(embed=em)
            return
        else:
            em.set_image(url='https:' + str(weeblist['posts']['post'][0]['@file_url']))
            msg = await self.bot.say(embed=em)
            await self.bot.add_reaction(msg, '◀')
            await self.bot.add_reaction(msg, '▶')
            await self.bot.add_reaction(msg, '❌')
            page = 0
            def check(reaction, user):
                if user.bot:
                    return False
                return True

            while True:
                res = await self.bot.wait_for_reaction(
                    ['◀', '▶', '❌'],
                    timeout=300,
                    message=msg,
                    check=check
                )
                if res is None:
                    await self.bot.clear_reactions(msg)
                    return
                elif res.reaction.emoji == '❌':
                    await self.bot.clear_reactions(msg)
                    return
                elif res.reaction.emoji == '◀':
                    await self.bot.remove_reaction(msg, res.reaction.emoji, res.user)
                    if page > 0:
                        page -= 1
                elif res.reaction.emoji == '▶':
                    await self.bot.remove_reaction(msg, res.reaction.emoji, res.user)
                    if page < numOfResults - 1:
                        page += 1
                imgurl = 'https:' + str(weeblist['posts']['post'][page]['@file_url'])
                em.set_image(url=imgurl)
                em.description = str(page+1) + ' / ' + str(numOfResults)
                em.url = imgurl
                await self.bot.edit_message(msg, embed=em)


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

    @commands.command(pass_context=True)
    async def sauce(self, ctx, *, search: str):
        pass

def setup(bot):
    bot.add_cog(Search(bot))
