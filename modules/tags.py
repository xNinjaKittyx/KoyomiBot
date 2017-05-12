
import asyncio
import discord
from discord.ext import commands
import redis
from utility import discordembed as dmbd


class Tags:

    def __init__(self, bot):
        self.bot = bot
        self.redis_db = redis.StrictRedis(host="localhost", port="6379", db=0)
        if not self.redis_db.hexists('tags', 'lol'):
            self.redis_db.hmset('tags', {'lol': 'xD'})

    @commands.group(pass_context=True)
    async def tag(self, ctx):
        """ Tags cannot be less than 3 fyi..."""
        if ctx.invoked_subcommand is None:
            query = ctx.message.content.split(sep=' ', maxsplit=1)[1]
            result = self.redis_db.hget('tags', query)
            if result is not None:
                await self.bot.say(result.decode('utf-8'))
            else:
                await self.bot.say("Tag doesn't exist.")

    @tag.command(pass_context=True)
    async def add(self, ctx, *, tag: str):

        if tag is None:
            return
        if len(tag) < 3 or len(tag) > 32:
            return
        if self.redis_db.hexists('tags', tag):
            await self.bot.say('Tag already exists. Sorry.')
        else:
            asdf = await self.bot.say("Waiting for content to go with the tag.")
            value = await self.bot.wait_for_message(
                timeout=15,
                author=ctx.message.author,
                channel=ctx.message.channel
            )
            await self.bot.delete_message(asdf)
            if value is None:
                await self.bot.say("Timed out. Try again.")
                return
            self.redis_db.hmset('tags', {tag: value.content})
            await self.bot.say("Tag Added")

    @tag.command(pass_context=True)
    async def search(self, ctx, *, query: str):
        if query is None:
            return
        results = []
        for x in self.redis_db.hkeys('tags'):
            if query in x.decode('utf-8'):
                results.append(x.decode('utf-8'))
        wew = ""
        for x, y in enumerate(results):
            wew += str(x+1) + ") " + results[x] + "\n"
        em = discord.Embed()
        em.set_footer(text=wew)
        await self.bot.say(embed=em)

    @tag.command(pass_context=True)
    async def delete(self, ctx, *, query: str):
        if query is None:
            return
        if not self.bot.cogs['Admin'].checkdev(ctx.message.author.id):
            return
        for x in self.redis_db.hkeys('tags'):
            print(x.decode('utf-8'))
            if query == x.decode('utf-8'):
                if self.redis_db.hdel('tags', query) == 1:
                    await self.bot.say("Tag Deleted")

def setup(bot):
    """ Setup Tags.py"""
    bot.add_cog(Tags(bot))
