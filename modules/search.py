
# -*- coding: utf8 -*-
import logging
import random
import xmltodict

from discord.ext import commands
import ujson
import wikipedia

import utility.discordembed as dmbd


class Search:

    def __init__(self, bot):
        self.bot = bot

    async def gfylink(self, keyword, count, author):
        link = "https://api.gfycat.com/v1/gfycats/search?search_text=" + str(keyword) + "&count=" + str(count)

        async with self.bot.session.get(link) as r:
            if r.status != 200:
                logging.error('Gyfcat returned ' + r.status)
            giflist = await r.json(loads=ujson.loads)
            num = random.randint(0, count-1)
            gif = giflist["gfycats"][num]
            title = gif["gfyName"]
            desc = gif["title"]
            if gif["tags"] is not None:
                desc += " #" + " #".join([x for x in gif["tags"]])

            url = "https://gfycat.com/" + title
            return dmbd.newembed(author, title, desc, url)

    @commands.command()
    async def owgif(self, ctx):
        """Random Overwatch Gyfcat"""
        em = await self.gfylink("overwatch", 100, ctx.author)
        await ctx.send(embed=em)
        await ctx.send(em.url)
        await self.bot.cogs['Wordcount'].cmdcount('owgif')

    @commands.command()
    async def gfy(self, ctx, *, keyword: str):
        """Does a search on gyfcat"""
        em = await self.gfylink(keyword, 50, ctx.author)
        await ctx.send(embed=em)
        await ctx.send(em.url)
        await self.bot.cogs['Wordcount'].cmdcount('gfy')

    @commands.command()
    async def safebooru(self, ctx, *, search: str):
        """Searches Safebooru"""

        await self.bot.cogs['Wordcount'].cmdcount('safebooru')
        link = ("https://safebooru.org/index.php?page=dapi&s=post&q=index&limit=20&tags=" +
                search.replace(' ', '_'))

        async with self.bot.session.get(link) as r:
            if r.status != 200:
                self.bot.cogs['Log'].output('[WARNING]: Safebooru Search Failed')
            weeblist = xmltodict.parse(await r.text())
            weeblist = weeblist['posts']['post']

        results = len(weeblist)

        title = 'Safebooru: ' + search
        sample_url = 'https:{0[@sample_url]}'
        file_url = 'https:{0[@file_url]}'
        desc = '{0} / ' + str(results)
        source = '[Here]({0[@source]})'
        em = dmbd.newembed(ctx.author, title)
        if results == 0:
            em.description = "No Results Found For " + search
            await ctx.send(embed=em)
            return
        elif results == 1:
            em.set_image(url=sample_url.format(weeblist))
            em.url = file_url.format(weeblist)
            em.description = desc.format(1)
            em.add_field(name='Source', value=source.format(weeblist))
            em.add_field(name='Tags', value=weeblist['@tags'])
            await ctx.send(embed=em)
            return
        else:
            em.set_image(url=sample_url.format(weeblist[0]))
            em.url = file_url.format(weeblist[0])
            em.description = desc.format(1)
            em.add_field(name='Source', value=source.format(weeblist[0]))
            em.add_field(name='Tags', value=weeblist[0]['@tags'])
            msg = await ctx.send(embed=em)
            await msg.add_reaction('◀')
            await msg.add_reaction('▶')
            await msg.add_reaction('❌')
            page = 0

            def check(reaction, user):
                if user.bot:
                    return False
                return str(reaction.emoji) in ['◀', '▶', '❌'] and reaction.message.id == msg.id

            while True:
                try:
                    res, user = await self.bot.wait_for(
                        'reaction_add',
                        check=check,
                        timeout=300,
                    )
                except TimeoutError:
                    await msg.clear_reactions()
                    return
                if res is None:
                    await msg.clear_reactions()
                    return
                elif res.emoji == '❌':
                    await msg.clear_reactions()
                    return
                elif res.emoji == '◀':
                    await msg.remove_reaction(res.emoji, user)
                    if page > 0:
                        page -= 1
                elif res.emoji == '▶':
                    await msg.remove_reaction(res.emoji, user)
                    if page < results - 1:
                        page += 1

                em.set_image(url=sample_url.format(weeblist[page]))
                em.url = file_url.format(weeblist[page])
                em.description = desc.format(page+1)
                em.clear_fields()
                em.add_field(name='Source', value=source.format(weeblist[page]))
                em.add_field(name='Tags', value=weeblist[page]['@tags'])
                await msg.edit(embed=em)

    @commands.command()
    async def konachan(self, ctx, *, search: str):
        """Searches Konachan (rating:safe)"""
        await self.bot.cogs['Wordcount'].cmdcount('konachan')
        link = ("https://konachan.com/post.json?limit=20&tags=rating:safe%20" +
                search.replace('rating:questionable', '').replace('rating:explicit', ''))

        async with self.bot.session.get(link) as r:
            if r.status != 200:
                self.bot.cogs['Log'].output('[WARNING]: Konachan Search Failed')
            weeblist = await r.json(loads=ujson.loads)

        results = len(weeblist)

        title = 'Konachan: ' + search
        desc = '{0} / ' + str(results)
        source = '[Here]({0[source]})'
        em = dmbd.newembed(ctx.author, title)
        if results == 0:
            em.description = "No Results Found For " + search
            await ctx.send(embed=em)
            return
        elif results == 1:
            em.set_image(url='https:' + weeblist[0]['sample_url'])
            em.url = 'http:' + weeblist[0]['file_url']
            em.description = desc.format(1)
            em.add_field(name='Source', value=source.format(weeblist[0]))
            em.add_field(name='Tags', value=weeblist[0]['tags'])
            await ctx.send(embed=em)
            return
        else:
            em.set_image(url='https:' + weeblist[0]['sample_url'])
            em.url = 'http:' + weeblist[0]['file_url']
            em.description = desc.format(1)
            em.add_field(name='Source', value=source.format(weeblist[0]))
            em.add_field(name='Tags', value=weeblist[0]['tags'])
            msg = await ctx.send(embed=em)
            await msg.add_reaction('◀')
            await msg.add_reaction('▶')
            await msg.add_reaction('❌')
            page = 0

            def check(reaction, user):
                if user.bot:
                    return False
                return str(reaction.emoji) in ['◀', '▶', '❌'] and reaction.message.id == msg.id

            while True:
                try:
                    res, user = await self.bot.wait_for(
                        'reaction_add',
                        check=check,
                        timeout=300,
                    )
                except TimeoutError:
                    await msg.clear_reactions()
                    return
                if res is None:
                    await msg.clear_reactions()
                    return
                elif res.emoji == '❌':
                    await msg.clear_reactions()
                    return
                elif res.emoji == '◀':
                    await msg.remove_reaction(res.emoji, user)
                    if page > 0:
                        page -= 1
                elif res.emoji == '▶':
                    await msg.remove_reaction(res.emoji, user)
                    if page < results - 1:
                        page += 1

                em.set_image(url='https:' + weeblist[page]['sample_url'])
                em.url = 'http:' + weeblist[page]['file_url']
                em.description = desc.format(page+1)
                em.clear_fields()
                em.add_field(name='Source', value=source.format(weeblist[page]))
                em.add_field(name='Tags', value=weeblist[page]['tags'])
                await msg.edit(embed=em)

    @commands.command()
    async def urban(self, ctx, *, search: str):
        """ Searches Urban Dictionary. """
        async with self.bot.session.get('https://api.urbandictionary.com/v0/define?term=' + search) as r:
            if r.status != 200:
                self.bot.cogs['Log'].output('Urban Dictionary is Down')
            results = await r.json(loads=ujson.loads)

        if results['result_type'] != 'exact':
            em = dmbd.newembed(ctx.author, 'Urban Dictionary', 'No Results Found For' + search)
            await ctx.send(embed=em)
            return
        size = len(results['list'])
        definition = results['list'][random.randint(0, size-1)]
        title = definition['word']
        url = definition['permalink']
        define = definition['definition']
        thumbs_up = definition['thumbs_up']
        thumbs_down = definition['thumbs_down']
        example = definition['example']
        author = definition['author']
        desc = 'Defined by: {0}\n{1}\n\nExample: {2}\n\n👍{3}\t👎{4}'.format(author, define, example, thumbs_up, thumbs_down)
        em = dmbd.newembed(ctx.author, t=title, d=desc, u=url)
        await ctx.send(embed=em)

    @commands.command()
    async def wiki(self, ctx, *, search: str):
        """ Grabs Wikipedia Article """
        searchlist = wikipedia.search(search)
        if len(searchlist) < 1:
            title = "Searched for: " + search
            desc = 'No Results Found'
            em = dmbd.newembed(ctx.author, title, desc)
            await ctx.send(embed=em)
        else:
            page = wikipedia.page(searchlist[0])

            title = page.title
            desc = wikipedia.summary(searchlist[0], 3)
            url = page.url
            em = dmbd.newembed(ctx.author, title, desc, url)

            em.set_image(url=page.images[0])
            em.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Wikipedia-logo-v2-en.svg/250px-Wikipedia-logo-v2-en.svg.png")
            await self.bot.cogs['Wordcount'].cmdcount('wiki')
            await ctx.send(embed=em)

    @commands.command()
    async def sauce(self, ctx, *, search: str):
        """ In Progress... Will return sauce of any linked photo. """
        pass


def setup(bot):
    bot.add_cog(Search(bot))
