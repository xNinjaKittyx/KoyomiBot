import logging
import time
from typing import Optional

import discord
from discord.ext import commands

import koyomibot.utility.discordembed as dmbd
from koyomibot.main import MyClient

log = logging.getLogger(__name__)


class Info(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot
        self.initialtime = time.time()

    def getuptime(self):
        seconds = int(time.time() - self.initialtime)
        minutes = 0
        hours = 0
        days = 0

        if seconds > 86399:
            days = int(seconds / 86400)
            seconds = seconds % 86400
        if seconds > 3599:
            hours = int(seconds / 3600)
            seconds = seconds % 3600
        if seconds > 59:
            minutes = int(seconds / 60)
            seconds = seconds % 60

        return f"{days}d {hours}h {minutes}m {seconds}s"

    @commands.command()
    async def ping(self, ctx):
        em = dmbd.newembed(ctx.author, d=str(self.bot.latency))
        await ctx.send(embed=em)

    @commands.command()
    async def stats(self, ctx):
        author = ctx.author
        title = "Stats for " + self.bot.user.name
        desc = "Don't..t..t... look at my stats... Baka!"
        url = "https://github.com/xNinjaKittyx/"
        inviteurl = (
            "https://discordapp.com/api/oauth2/authorize?client_id="
            + str(self.bot.user.id)
            + "&scope=bot&permissions=0"
        )

        supporturl = "https://discord.gg/Fzz344U"

        em = dmbd.newembed(author, title, desc, url)
        em.add_field(name="Total Users", value=len(self.bot.users))
        em.add_field(name="Total Guilds", value=len(self.bot.guilds))
        em.add_field(name="Current Guild Users", value=len(ctx.guild.members))
        em.add_field(name="Uptime", value=self.getuptime())
        em.add_field(name="Invite", value=f"[Click Me :)]({inviteurl})")
        em.add_field(name="Support", value=f"[Discord Link]({supporturl})")

        await ctx.send(embed=em)

    @commands.command()
    async def uptime(self, ctx):
        await ctx.send("```" + self.getuptime() + "```")

    def _get_discord_member(self, ctx: commands.Context, discord_id: Optional[str]) -> discord.Member:

        if discord_id is None:
            member = ctx.author
        else:
            discord_id = str(discord_id)
            for person in ctx.guild.members:
                log.info(discord_id)
                log.info((str(person.id), str(person.name), str(person.nick)))
                if discord_id in (str(person.id), str(person.name), str(person.nick)):
                    member = person
                    log.info(member.avatar_url)
                    break
            else:
                raise Exception(f"Could not find discord member with {discord_id}")

        return member

    @commands.command(aliases=["av"])
    async def avatar(self, ctx, discord_id: Optional[str] = None) -> None:

        member = self._get_discord_member(ctx, discord_id)
        if member is None:
            return

        log.info(member.avatar_url)
        em = dmbd.newembed(member)
        em.set_image(url=member.avatar_url)
        log.info(em.to_dict())
        await ctx.send(embed=em)

    @commands.command()
    async def me(self, ctx: commands.Context, discord_id: Optional[str] = None) -> None:
        member = self._get_discord_member(ctx, discord_id)
        if member is None:
            return

        em = dmbd.newembed(member, f"{member.name}#{member.discriminator} ({member.nick})", member.id)
        em.set_thumbnail(url=member.avatar_url)

        em.add_field(name="Status", value=member.raw_status)
        em.add_field(name="Activity", value=str(member.activity))
        em.add_field(name="Created At", value=member.created_at)
        em.add_field(name="Joined At", value=member.joined_at)
        em.add_field(name="Premium Since", value=member.premium_since)

        await ctx.send(embed=em)


def setup(bot: MyClient) -> None:
    bot.add_cog(Info(bot))
