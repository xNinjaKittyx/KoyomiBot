
import random
import time

from discord.ext import commands
import utility.discordembed as dmbd


class Profile:

    def __init__(self, bot):
        self.bot = bot
        self.EXP_CURVE = 1 / 1.5
        self.EXP_BOOST = 1
        """ So in this section, there's going to be some way of having "points"
        and therefore leveling up after reaching x number of points.

        First we need to set some sort of leveling system.

        exp curve. Start with 100, then increase x^1.8 per leve

        base_xp * (level_to_get ^ factor) = exp required for level_to_get


        expreq / base_xp ^ (1/factor) = level_to_get

        1) Avatar. If someone looks you up, you can get a small exp between 1 - 5
        2) Chatting? Maybe each message will give you 0.1 exp?
        3) Perhaps a game where you bet any available exp. Lowstakes, highstakes.
        lowstakes will give you 1.25x exp back, but high stake will give you 1.5x back...
        Expected value of lowstake (50%) will be 0.625x exp...
        Expected Value of highstake (33%) will be 0.495x exp..

        """
    def newuser(self, author, xp, timestamp=0):
        if author.bot:
            return
        self.bot.redis_db.lpush(author.id, author.name + "#" + author.discriminator)
        self.bot.redis_db.lpush(author.id, xp)
        self.bot.redis_db.lpush(author.id, timestamp)

    def addpoints(self, author, xp, cooldown=0):
        xp = xp * self.EXP_BOOST
        if self.bot.redis_db.exists(author.id):
            timestamp = self.bot.redis_db.lindex(author.id, 0).decode('utf-8')
            xp += int(self.bot.redis_db.lindex(author.id, 1).decode('utf-8'))
            if int(time.time()) - int(timestamp) > cooldown:

                self.bot.redis_db.lset(author.id, 0, timestamp)
                self.bot.redis_db.lset(author.id, 1, xp)
        else:
            self.newuser(author, xp, int(time.time()))

    @staticmethod
    def getuser(ctx, name):
        if name is None:
            return ctx.message.author
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = ctx.message.server.get_member_named(name)
        if not user:
            name = name.lower()
            for x in ctx.message.server.members:
                if x.name.lower() == name:
                    return user
                elif x.nick:
                    if x.nick.lower() == name:
                        return user
        return user

    def getlevel(self, authorid):
        if self.bot.redis_db.exists(authorid):
            xp = int(self.bot.redis_db.lindex(authorid, 1).decode('utf-8'))
            total = ((xp/100)**self.EXP_CURVE) + 1
            lvl = int(total)
            percent = total - lvl
            return lvl, percent
        else:
            return 1, 0

    async def on_message(self, msg):
        if msg.author.bot:
            return
        if msg.server is None:
            return
        if msg.server.id == 264445053596991498 or msg.server.id == 110373943822540800:
            return
        self.addpoints(msg.author, random.randint(5, 20), 180)

    @commands.command(pass_context=True)
    async def avatar(self, ctx, *, name: str):
        """ Grabbing an avatar of a person """

        user = self.getuser(ctx, name)

        if not user:
            return
        author = ctx.message.author
        em = dmbd.newembed(author, u=user.avatar_url)
        em.set_image(url=user.avatar_url)
        em.add_field(name=user.name + '#' + user.discriminator + '\'s Avatar', value="Sugoi :D")

        if author != user:
            self.addpoints(user, random.randint(1, 5))

        await self.bot.say(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('avatar')

    @commands.command(pass_context=True)
    async def profile(self, ctx, *,  name: str):
        """ Display Profile :o """

        user = self.getuser(ctx, name)
        if not user:
            return
        author = ctx.message.author
        em = dmbd.newembed(author, user.name + '#' + user.discriminator, u=user.avatar_url)
        em.set_image(url=user.avatar_url)
        lvl, percent = self.getlevel(user.id)
        em.add_field(name="Lv. " + str(lvl), value=str(int(percent * 100)) + "%")
        await self.bot.say(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('profile')


def setup(bot):
    bot.add_cog(Profile(bot))
