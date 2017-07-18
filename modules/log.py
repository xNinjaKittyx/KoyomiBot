
# -*- coding: utf8 -*-
import codecs
from datetime import datetime
import os

from discord.utils import find


class Log:
    def __init__(self, bot):
        self.bot = bot

    # All them event overrides....
    async def on_message(self, msg):
        if msg.content.startswith(self.bot.command_prefix):
            cmd_used = msg.author.name + " attempted to use the command: " + msg.content
            self.bot.logger.info(cmd_used)
            if msg.guild:
                mod_log = find(lambda c: c.name == "modlog", msg.guild.channels)
                if mod_log is None:
                    return
                await mod_log.send(cmd_used)

    async def on_member_join(self, member):
        try:
            self.bot.logger.info(member.name + " has joined the guild at " + member.guild.name)
        except UnicodeEncodeError:
            self.bot.logger.info(
                member.name.encode('ascii', 'ignore').decode('ascii', 'ignore') +
                " has joined the guild at " +
                member.guild.name.encode('ascii', 'ignore').decode('ascii', 'ignore')

            )

    async def on_member_remove(self, member):
        try:
            self.bot.logger.info(member.name + " has left the guild at " + member.guild.name)
        except UnicodeEncodeError:
            self.bot.logger.info(
                member.name.encode('ascii', 'ignore').decode('ascii', 'ignore') +
                " has left the guild at " +
                member.guild.name.encode('ascii', 'ignore').decode('ascii', 'ignore')
            )

    async def on_message_delete(self, msg):
        if msg.author == self.bot.user:
            return
        result = '{0} deleted the following message: \n{1}'.format(msg.author.name, msg.content)

        if msg.guild:
            mod_log = find(lambda c: c.name == "modlog", msg.guild.channels)
            if mod_log is None:
                return
            await mod_log.send(result)

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
        if before.guild:
            mod_log = find(lambda c: c.name == "modlog", before.guild.channels)
            if mod_log is None:
                return
            await mod_log.send(msg)


def setup(bot):
    """Setup Log.py"""
    bot.add_cog(Log(bot))
