
import codecs
from datetime import datetime
import os

from discord.utils import find


class Log:
    def __init__(self, bot):
        self.bot = bot

    # All them event overrides....
    async def on_message(self, msg):
        if await self.bot.check_blacklist(msg):
            cmd_used = f"{msg.author.name} <@{msg.author.id}> used command in {msg.guild.name}/{msg.guild.id}: {msg.content}"
            self.bot.logger.info(cmd_used)
            if msg.guild:
                mod_log = find(lambda c: c.name == "modlog", msg.guild.channels)
                if mod_log is None:
                    return
                await mod_log.send(cmd_used)

    async def on_member_join(self, member):
        if member.guild.id in [264445053596991498, 110373943822540800]:
            # Hardcoding ignores for two discord bot servers.
            # TODO: Needs a json list of servers to ignore.
            return
        try:
            self.bot.logger.info(
                f"{member.name} <@{member.id}> has joined the guild at {member.guild.name}/{member.guild.id}")
        except UnicodeEncodeError:
            self.bot.logger.info(
                f"{member.name.encode('ascii', 'ignore').decode('ascii', 'ignore')} <@{member.id}>"
                " has joined the guild at "
                f"{member.guild.name.encode('ascii', 'ignore').decode('ascii', 'ignore')}/{member.guild.id}"

            )

    async def on_member_remove(self, member):
        if member.guild.id in [264445053596991498, 110373943822540800]:
            # Hardcoding ignores for two discord bot servers.
            return
        try:
            self.bot.logger.info(
                f"{member.name} <@{member.id}> has left the guild at {member.guild.name}/{member.guild.id}")
        except UnicodeEncodeError:
            self.bot.logger.info(
                f"{member.name.encode('ascii', 'ignore').decode('ascii', 'ignore')} <@{member.id}>"
                " has left the guild at "
                f"{member.guild.name.encode('ascii', 'ignore').decode('ascii', 'ignore')}/{member.guild.id}"
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
