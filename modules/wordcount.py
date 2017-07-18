""" Counting Words :o """
import re

from discord.ext import commands
import utility.discordembed as dmbd


class Wordcount:

    def __init__(self, bot):
        self.bot = bot
        self.blacklist = ['the', 'and', 'for', 'are', 'but', 'not', 'you',
                          'all', 'any', 'can', 'her', 'was', 'one', 'our',
                          'out', 'day', 'get', 'has', 'him', 'his', 'how',
                          'man', 'new', 'now', 'old', 'see', 'two', 'way',
                          'who', 'boy', 'did', 'its', 'let', 'put', 'say',
                          'she', 'too', 'use', 'dad', 'mom']

    def cmdcount(self, name: str):
        self.bot.redis_db.zincrby('CmdDB', name)

    async def wordcount(self, content):
        for x in re.compile('\w+').findall(content.replace('\n', ' ')):
            if len(x) <= 2:
                continue
            if x.startswith('http'):
                continue
            if x in self.blacklist:
                continue
            else:
                self.bot.redis_db.zincrby('WordDB', x)

    async def on_message(self, message):
        if (len(message.content) <= 2 or message.author.bot or
                message.content.startswith(self.bot.command_prefix)):
            return
        await self.wordcount(message.content)

    @commands.command()
    async def topwords(self, ctx):
        """Top 10 words used in all guilds."""
        title = "Top 10 Words Used"
        desc = "This is counted across all guilds " + self.bot.user.name + " is on."
        em = dmbd.newembed(ctx.author, title, desc)
        for x in self.bot.redis_db.zrevrange('WordDB', 0, 9, withscores=True):
            em.add_field(name=x[0].decode('utf-8'), value=int(x[1]))

        await ctx.send(embed=em)
        self.cmdcount('topwords')

    @commands.command()
    async def wordused(self, ctx, word: str):
        """ Shows how many times a word has been used."""

        num = int(self.bot.redis_db.zscore('WordDB', word))
        if num == 0:
            title = "This word has never been used yet :o"
        elif num == 1:
            title = "This word has been used only once."
        else:
            title = "This word has been used {} times.".format(num)

        desc = "This is counted across all guilds " + self.bot.user.name + " is on."
        em = dmbd.newembed(ctx.author, title, desc)

        await ctx.send(embed=em)
        self.cmdcount('wordused')

    @commands.command()
    async def blackwords(self, ctx):
        """ Words that are not included in wordDB"""
        result = " ".join(self.blacklist)
        await ctx.send("```\n" + result + "\nGrabbed from YourDictionary as the most common three letter words.\n```")
        self.cmdcount('blackwords')

    @commands.command()
    async def topcmds(self, ctx):
        """ Top 10 cmds used."""
        author = ctx.message.author
        title = "Top 10 Commands Used"
        desc = "This is counted across all guilds " + self.bot.user.name + " is on."
        em = dmbd.newembed(author, title, desc)
        for x in self.bot.redis_db.zrevrange('CmdDB', 0, 9, withscores=True):
            em.add_field(name=x[0].decode('utf-8'), value=int(x[1]))

        await ctx.send(embed=em)
        self.cmdcount('topcmds')

    @commands.command()
    async def cmdused(self, ctx, word: str):
        """ Shows how many times a cmd has been used."""
        num = int(self.bot.redis_db.zscore('CmdDB', word))
        if num == 0:
            title = "This command has never been used yet :o"
        elif num == 1:
            title = "This command has been used only once."
        else:
            title = "This command has been used {} times.".format(num)

        desc = "This is counted across all guilds " + self.bot.user.name + " is on."
        em = dmbd.newembed(ctx.author, title, desc)

        await ctx.send(embed=em)
        self.cmdcount('cmdused')


def setup(bot):
    bot.add_cog(Wordcount(bot))
