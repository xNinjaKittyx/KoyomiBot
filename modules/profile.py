
import random
import time

from discord.ext import commands
import redis
import utility.discordembed as dmbd


class KoyomiUser:
    def __init__(self, author):
        self.redis_db = redis.StrictRedis(db=1)
        self.author_id = author.id
        if not self.redis_db.exists(author.id):
            default_profile = {
                'cooldown': 0,
                'xp': 0,
                'name': author.name + "#" + author.discriminator,
                'coins': 0,
                'level': 0
            }
            self.redis_db.hmset(author.id, default_profile)

    def get_field(self, key):
        return self.redis_db.hget(self.author_id, key).decode('utf-8')

    def set_field(self, key, value):
        return self.redis_db.hset(self.author_id, key, value)

    def get_cooldown(self):
        return int(self.get_field('cooldown'))

    def set_cooldown(self):
        self.redis_db.hset(self.author_id, 'cooldown', int(time.time()))

    def get_xp(self):
        return int(self.get_field('xp'))

    def get_name(self):
        return str(self.get_field('name'))

    def get_coins(self):
        return int(self.get_field('coins'))

    def get_level(self):
        return int(self.get_field('level'))

    def get_required_xp(self):
        level_to_get = self.get_level() + 1
        return int(100 + level_to_get ** 1.5)

    def check_cooldown(self, seconds):
        if int(time.time()) - self.get_cooldown() > seconds:
            return True
        return False

    def add_xp(self, xp):
        self.redis_db.hincrby(self.author_id, 'xp', xp)
        if self.get_xp() > self.get_required_xp():
            # the player leveled up!
            self.redis_db.hincrby(self.author_id, 'coins', 100)
            self.redis_db.hincrby(self.author_id, 'level', 1)
            return True

    def add_coins(self, coins):
        self.redis_db.hincrby(self.author_id, 'coins', coins)

    def use_coins(self, coins):
        current_coins = self.get_coins()
        if current_coins > coins:
            self.redis_db.hincrby(self.author_id, 'coins', -coins)


class Profile:

    def __init__(self, bot):
        self.bot = bot
        self.users = {} # userid: KoyomiUser
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

    @staticmethod
    def getuser(ctx, name=None):
        if name is None:
            return ctx.author
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = ctx.guild.get_member_named(name)
        if not user:
            name = name.lower()
            for x in ctx.guild.members:
                if x.name.lower() == name:
                    return user
                elif x.nick:
                    if x.nick.lower() == name:
                        return user
        return user

    def get_koyomi_user(self, userid):
        if userid in self.users:
            user = self.users[userid]
        else:
            user = KoyomiUser(userid)
            self.users[userid] = user
        return user

    async def on_message(self, msg):
        if msg.author.bot:
            return
        if msg.guild is None:
            return
        if msg.guild.id == 264445053596991498 or msg.guild.id == 110373943822540800:
            return

        user = self.get_koyomi_user(msg.author.id)
        user.add_xp(random.randint(5, 20))

    @commands.command()
    async def avatar(self, ctx, *, name: str=None):
        """ Grabbing an avatar of a person """

        user = self.getuser(ctx, name)

        if not user:
            return
        author = ctx.author
        em = dmbd.newembed(author, u=user.avatar_url)
        em.set_image(url=user.avatar_url)
        em.add_field(name=user.name + '#' + user.discriminator + '\'s Avatar', value="Sugoi :D")

        if author != user:
            self.addpoints(user, random.randint(1, 5))

        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('avatar')

    @commands.command()
    async def profile(self, ctx, *,  name: str=None):
        """ Display Profile :o """

        user = self.getuser(ctx, name)
        if not user:
            return
        author = ctx.author
        userfull = user.name + '#' + user.discriminator
        em = dmbd.newembed(author, userfull , u=user.avatar_url)
        em.set_image(url=user.avatar_url)
        lvl, percent = self.getlevel(user.id)
        em.add_field(name='Username', value=userfull)
        em.add_field(name='UserID', value=user.id)
        em.add_field(name="Lv. " + str(lvl), value=str(int(percent * 100)) + "%")
        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('profile')


def setup(bot):
    bot.add_cog(Profile(bot))
