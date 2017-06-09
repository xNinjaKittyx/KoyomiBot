
from discord.ext import commands
from utility import discordembed as dmbd


class Tags:

    def __init__(self, bot):
        self.bot = bot
        if not bot.redis_db.hexists('tags', 'lol'):
            bot.redis_db.hmset('tags', {'lol': 'xD'})

    @commands.group()
    async def tag(self, ctx):
        """ Tags cannot be less than 3 fyi..."""
        if ctx.invoked_subcommand is None:
            query = ctx.message.content.split(sep=' ', maxsplit=1)[1]
            result = self.bot.redis_db.hget('tags', query)
            if result is not None:
                await ctx.send(result.decode('utf-8'))
            else:
                return

    @tag.command()
    async def add(self, ctx, *, tag: str):

        if tag is None:
            return
        if len(tag) < 3 or len(tag) > 32:
            return
        if self.bot.redis_db.hexists('tags', tag):
            await ctx.send('Tag already exists. Sorry.')
        else:
            asdf = await ctx.send("Waiting for content to go with the tag.")

            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel
            value = await self.bot.wait_for_message(
                'message',
                check=check,
                timeout=15
            )
            await asdf.delete()
            if value is None:
                await ctx.send("Timed out. Try again.")
                return
            self.bot.redis_db.hmset('tags', {tag: value.content})
            await ctx.send("Tag Added")

    @tag.command()
    async def search(self, ctx, *, query: str):
        if query is None:
            return
        results = []
        for x in self.bot.redis_db.hkeys('tags'):
            if query in x.decode('utf-8'):
                results.append(x.decode('utf-8'))
        wew = ""
        for x, y in enumerate(results):
            wew += str(x+1) + ") " + y + "\n"
        em = dmbd.newembed(ctx.author)
        em.set_footer(text=wew)
        await ctx.send(embed=em)

    @tag.command()
    async def delete(self, ctx, *, query: str):
        if query is None:
            return
        if not self.bot.checkdev(ctx.author.id):
            return
        for x in self.bot.redis_db.hkeys('tags'):
            print(x.decode('utf-8'))
            if query == x.decode('utf-8'):
                if self.bot.redis_db.hdel('tags', query) == 1:
                    await ctx.send("Tag Deleted")

def setup(bot):
    """ Setup Tags.py"""
    bot.add_cog(Tags(bot))
