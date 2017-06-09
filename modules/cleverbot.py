from cleverwrap import CleverWrap


class Cleverbot:
    def __init__(self, bot):
        self.bot = bot
        self.cleverbot = CleverWrap(bot.redis_db.get('CleverbotAPI'))

    async def on_message(self, msg):
        if msg.content.startswith(self.bot.user.mention):
            namae = len(self.bot.user.mention)
            await msg.channel.send(self.cleverbot.say(msg.content[namae:]))


def setup(bot):
    """Setup Anime.py"""
    bot.add_cog(Cleverbot(bot))