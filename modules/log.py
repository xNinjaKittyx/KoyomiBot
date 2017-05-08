
from datetime import datetime
import os

import discord
from discord.ext import commands
from discord.utils import find


class Log:
    def __init__(self, bot):
        self.bot = bot

    def output(self, a):
        """ Output the string 'a' """
        today = datetime.today()
        filename = "log-{0}-{1}-{2}.log".format(str(today.month), str(today.day), str(today.year))
        prefix = "[{0}:{1}:{2}]: ".format(str(today.hour), str(today.minute), str(today.second))
        print(prefix + a)
        if not os.path.exists('./logs'):
            os.makedirs('./logs')
        with open('./logs/' + filename, 'a') as f:
            f.write(prefix + a + "\n")
            f.close()

    # All them event overrides....
    async def on_message(self, msg):
        if msg.content.startswith(self.bot.command_prefix):
            cmdused = msg.author.name + " attempted to use the command: " + msg.content
            self.output(cmdused)
            modlog = find(lambda c: c.name == "modlog", msg.server.channels)
            if modlog == None:
                return
            await self.bot.send_message(modlog, cmdused)

    async def on_member_join(self, member):
        self.output(member.name + " has joined the server at " + member.server.name)

    async def on_member_remove(self, member):
        self.output(member.name + " has left the server at " + member.server.name)

    async def on_message_delete(self, msg):
        if msg.author == self.bot.user:
            return
        result = '{0} deleted the following message: \n{1}'.format(msg.author.name, msg.content)
        modlog = find(lambda c: c.name == "modlog", msg.server.channels)
        if modlog == None:
            return
        await self.bot.send_message(modlog, result)

    async def on_message_edit(self, before, after):
        if before.author == self.bot.user:
            return
        if before.content == after.content:
            return
        msg = '{0} edit the following message: \nBefore: {1}\n After: {2}'.format(
            before.author.name,
            before.content,
            after.content
        )
        modlog = find(lambda c: c.name == "modlog", before.server.channels)
        if modlog == None:
            return
        await self.bot.send_message(modlog, msg)

def setup(bot):
    """Setup Log.py"""
    bot.add_cog(Log(bot))
