import time

from discord.ext import commands
import psutil
import utility.discordembed as dmbd
from main import MyClient


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

    @staticmethod
    def getcpuusage():
        total = 0
        proc = psutil.Process()
        return proc.cpu_percent()

    @staticmethod
    def getmemusage():
        total = 0
        proc = psutil.Process()
        return proc.memory_info().rss / (1024 ** 2)

    @commands.command()
    async def ping(self, ctx):
        em = dmbd.newembed(ctx.author, d=self.bot.latency)
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
        if author.id == 82221891191844864:
            em.add_field(name="CPU", value=f"{self.getcpuusage():.2f}%")
            em.add_field(name="Memory", value=f"{self.getmemusage():.2f} MB")
        em.add_field(name="Invite", value=f"[Click Me :)]({inviteurl})")
        em.add_field(name="Support", value=f"[Discord Link]({supporturl})")

        await ctx.send(embed=em)

    @commands.command()
    async def uptime(self, ctx):
        await ctx.send("```" + self.getuptime() + "```")


def setup(bot: MyClient) -> None:
    bot.add_cog(Info(bot))
