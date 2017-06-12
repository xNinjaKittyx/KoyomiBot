
import io
import random
import time

import discord
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw, ImageOps
import redis
import utility.discordembed as dmbd


background_imgs = [
    'hanekawa1.png',
    'kaiki1.png',
    'koyomi1.png',
    'koyomi2.png',
    'tsukihi1.png'
]

class KoyomiUser:
    def __init__(self, author):
        self.redis_db = redis.StrictRedis(db=1)
        self.author_id = author.id
        if not self.redis_db.exists(author.id):
            default_profile = {
                'msg_cd': 0,
                'poke_cd': 0,
                'xp': 0,
                'name': author.name + "#" + author.discriminator,
                'coins': 30,
                'level': 1,
                'pokes_given': 0,
                'pokes_received': 0,

            }
            self.redis_db.hmset(author.id, default_profile)
        else:
            self.redis_db.hset(author.id, 'name', author.name + "#" + author.discriminator)

    def get_field(self, key):
        return self.redis_db.hget(self.author_id, key).decode('utf-8')

    def set_field(self, key, value):
        return self.redis_db.hset(self.author_id, key, value)

    def inc_field(self, key, amount):
        return self.redis_db.hincrby(self.author_id, key, amount)

    def get_cooldown(self, cooldown_type):
        return int(self.get_field(cooldown_type))

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

    def get_percent(self):
        return int((self.get_xp() / self.get_required_xp()) * 100)

    def get_pokes_given(self):
        return int(self.get_field('pokes_given'))

    def get_pokes_received(self):
        return int(self.get_field('pokes_received'))

    def set_cooldown(self, cooldown_type):
        self.redis_db.hset(self.author_id, cooldown_type, int(time.time()))

    def check_cooldown(self, cooldown_type, seconds):
        if int(time.time()) - self.get_cooldown(cooldown_type) > seconds:
            return True
        return False

    def add_xp(self, xp: int):
        self.inc_field('xp', xp)
        self.redis_db.hincrby(self.author_id, 'xp', xp)
        if self.get_xp() > self.get_required_xp():
            # the player leveled up!
            self.inc_field('coins', 100)
            self.inc_field('level', 1)
            self.set_field('xp', 0)
            return True

    def check_coins(self, coins):
        if self.get_coins() > coins:
            return True
        else:
            return False

    def add_coins(self, coins: int):
        self.redis_db.hincrby(self.author_id, 'coins', coins)

    def use_coins(self, coins: int):
        if self.check_coins(coins):
            self.redis_db.hincrby(self.author_id, 'coins', -coins)
        else:
            raise NameError('NotEnoughCoins')

    def give_coins(self, coins: int, koyomi_user):
        if self.check_coins(coins) and koyomi_user:
            self.use_coins(coins)
            koyomi_user.add_coins(coins)

    def poke(self, koyomi_user):
        if koyomi_user and self.check_cooldown('poke_cd', 3600):
            self.inc_field('pokes_given', 1)
            self.add_xp(300)
            koyomi_user.inc_field('pokes_received', 1)
            koyomi_user.add_coins(300)

    def text_at_angle(self, text, angle, font, color):

        txt = Image.new('RGBA', (500, 50))
        d = ImageDraw.Draw(txt)
        d.text((0,0), text, font=font, fill=255)
        txt=txt.rotate(angle, expand=1)
        txt=ImageOps.colorize(txt, (0,0,0,0), color)
        return txt

    async def get_profile(self, avatar_file, user):
        avatar_file = io.BytesIO(avatar_file)
        user_avatar = Image.open(avatar_file)
        user_avatar = user_avatar.resize((256, 256), Image.LANCZOS)

        background = Image.open('images/' + random.choice(background_imgs))
        background = background.resize((1024, 640), Image.LANCZOS)

        ui = Image.open('images/Koyomi_Background_Template.png')

        final = Image.new('RGBA', (1024, 640))
        final.paste(background)
        final.paste(user_avatar, (90, 101))
        final.paste(ui, (0, 0), ui)

        draw = ImageDraw.Draw(final)
        font12 = ImageFont.truetype('font/SourceHanSans-Normal.ttc', 12)
        font24 = ImageFont.truetype('font/SourceHanSans-Normal.ttc', 24)
        font28 = ImageFont.truetype('font/SourceHanSans-Normal.ttc', 28)
        draw.text((350,250), user.display_name + self.get_name()[-5:], font=font28, fill=(0,0,0))
        draw.text((26,2), 'Lv. ' + str(self.get_level()), font=font28, fill=(0,0,0))
        draw.text((350,290), 'ID: ' + str(user.id), font=font12, fill=(0,0,0))
        final.save('lmfao.png')

        f = io.BytesIO()
        final.save(f, format='PNG')
        del draw
        return f.getvalue()


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

    def get_koyomi_user(self, user):
        if user.id in self.users:
            koyomi_user = self.users[user.id]
        else:
            koyomi_user = KoyomiUser(user)
            self.users[user.id] = koyomi_user
        return koyomi_user

    async def on_message(self, msg):
        if msg.author.bot:
            return
        if msg.guild is None:
            return
        if msg.guild.id == 264445053596991498 or msg.guild.id == 110373943822540800:
            return

        user = self.get_koyomi_user(msg.author)

        if user.check_cooldown('msg_cd', 150):
            user.add_xp(random.randint(5, 20))
            user.set_cooldown('msg_cd')

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
            koyomiuser = self.get_koyomi_user(user)
            koyomiuser.add_xp(random.randint(1,5))

        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('avatar')

    @commands.command()
    async def give(self, ctx, *, args):
        args = args.split(' ', 1)
        coins = args[0]
        name = args[1]
        if not coins.isnumeric():
            await ctx.send('Wrong Syntax. {}give [coins] [user]'.format(self.bot.command_prefix))
            return

        user = self.getuser(ctx, name)
        if not user:
            return

        sender_koyomi_user = self.get_koyomi_user(ctx.author)
        recipient_koyomi_user = self.get_koyomi_user(user)

        sender_koyomi_user.give_coins(coins, recipient_koyomi_user)

    @commands.command()
    async def profile(self, ctx, *,  name: str=None):
        """ Display Profile :o """

        user = self.getuser(ctx, name)
        if not user:
            return
        koyomi_user = self.get_koyomi_user(user)
        author = ctx.author
        userfull = user.name + '#' + user.discriminator
        em = dmbd.newembed(author, userfull, u=user.avatar_url)
        em.set_image(url=user.avatar_url)
        lvl = koyomi_user.get_level()
        percent = koyomi_user.get_percent()

        em.add_field(name='Username', value=userfull)
        em.add_field(name='UserID', value=user.id)
        em.add_field(name="Lv. " + str(lvl), value='{}%'.format(percent))
        em.add_field(name="Bank", value='{} Aragis'.format(koyomi_user.get_coins()))
        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('profile')

    @commands.command()
    async def testprofile(self, ctx, *, name: str=None):

        user = self.getuser(ctx, name)
        if not user:
            return
        koyomi_user = self.get_koyomi_user(user)
        async with self.bot.session.get(user.avatar_url) as r:
            if r.status != 200:
                return
            user_avatar = await r.read()
            final = await koyomi_user.get_profile(user_avatar, user)

        picture = discord.File(final, filename=user.name + '.png')
        await ctx.send(file=picture)


def setup(bot):
    bot.add_cog(Profile(bot))
