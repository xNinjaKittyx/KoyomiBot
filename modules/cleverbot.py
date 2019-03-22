from cleverwrap import CleverWrap


class CleverBot:
    def __init__(self, bot):
        self.bot = bot
        self.cleverbot = CleverWrap(self.bot.config['CleverbotAPI'])

    async def on_message(self, msg):
        if msg.content.startswith(self.bot.user.mention):
            namae = len(self.bot.user.mention)
            with msg.channel.typing():
                await msg.channel.send(self.cleverbot.say(msg.content[namae:]))


def setup(bot):
    """Setup Anime.py"""
    bot.add_cog(CleverBot(bot))
