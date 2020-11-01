from discord.ext import commands


class Mail:
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.command()
    async def ticket(self, ctx, *, msg):
        """ Send a message to the developer."""
        app_info = await self.bot.application_info()
        await app_info.owner.send(
            f"Author: {ctx.author}\n"
            f"ID: {ctx.author.id}\n"
            f"Server: {ctx.guild}\n"
            f"Message: {ctx.message.content[8:]}"
        )
        await ctx.message.add_reaction("✅")


def setup(bot):
    bot.add_cog(Mail(bot))
