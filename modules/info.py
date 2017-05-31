
from datetime import datetime
import time

from discord.ext import commands
import psutil
import utility.discordembed as dmbd

class Info:

    def __init__(self, bot):
        self.bot = bot
        self.initialtime = time.time()
        self.totalmembers = set({})

    def getuptime(self):
        seconds = int(time.time() - self.initialtime)
        minutes = 0
        hours = 0
        days = 0

        if seconds > 86399:
            days = int(seconds/86400)
            seconds = seconds % 86400
        if seconds > 3599:
            hours = int(seconds/3600)
            seconds = seconds % 3600
        if seconds > 59:
            minutes = int(seconds/60)
            seconds = seconds % 60

        return "{d}d {h}h {m}m {s}s".format(d=days, h=hours, m=minutes, s=seconds)

    @staticmethod
    def getcpuusage():
        return psutil.Process().cpu_percent() / psutil.cpu_count()

    @staticmethod
    def getmemusage():
        return psutil.Process().memory_info().rss / (1024 ** 2)

    def gettotalusers(self):
        for x in self.bot.servers:
            for y in x.members:
                self.totalmembers.add(y.id)
        return len(self.totalmembers)

    @commands.command(pass_context=True)
    async def ping(self, ctx):
        pingpong = datetime.now() - ctx.message.timestamp
        pingpong = pingpong.microseconds / 1000
        second = await self.bot.say('*headtilt*')
        heartbeat = second.timestamp - ctx.message.timestamp
        heartbeat = heartbeat.microseconds / 1000
        description = (
            ':ping_pong: `' + str(pingpong) + ' ms`\n' +
            ':blue_heart: `' + str(heartbeat) + ' ms`'
        )
        em = dmbd.newembed(ctx.message.author, d=description)
        await self.bot.edit_message(second, new_content='',embed=em)

    @commands.command(pass_context=True)
    async def stats(self, ctx):
        author = ctx.message.author
        title = 'Stats for ' + self.bot.user.name
        desc = 'Don\'t..t..t... look at my stats... Baka!'
        url = "https://github.com/xNinjaKittyx/"
        # trello = "Add Later"
        inviteurl = (
            "https://discordapp.com/api/oauth2/authorize?client_id=" +
            self.bot.user.id +
            "&scope=bot&permissions=0"
        )

        supporturl = "https://discord.gg/Fzz344U"

        em = dmbd.newembed(author, title, desc, url)
        em.add_field(name='Total Users', value=self.gettotalusers())
        em.add_field(name='Total Servers', value=len(self.bot.servers))
        em.add_field(name='Current Server Users', value=len(ctx.message.server.members))
        em.add_field(name='Uptime', value=self.getuptime())
        em.add_field(name='CPU', value="{0:.2f}%".format(self.getcpuusage()))
        em.add_field(name='Memory', value="{0:.2f} MB".format(self.getmemusage()))
        # em.add_field(name='Trello', value='[Trello Page]({})'.format(trello))
        em.add_field(name='Invite', value='[Click Me :)]({})'.format(inviteurl))
        em.add_field(name='Support', value='[Discord Link]({})'.format(supporturl))

        await self.bot.say(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('stats')

    @commands.command()
    async def uptime(self):
        await self.bot.say("```" + self.getuptime() + "```")
        self.bot.cogs['Wordcount'].cmdcount('uptime')


def setup(bot):
    bot.add_cog(Info(bot))
