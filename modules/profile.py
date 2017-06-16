
import json
import io
import random
import time

import discord
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageColor

import redis
import utility.discordembed as dmbd


background_imgs = [
    'hanekawa1.png',
    'kaiki1.png',
    'koyomi1.png',
    'koyomi2.png',
    'tsukihi1.png',
    'mayoi1.png',
    'yotsugi1.png'
]

badges = {
    'discord': 0,
    'anotherbadge': 932,
    'etc': 102,
}
font12 = ImageFont.truetype('font/Aileron-Regular.otf', 12)
font24 = ImageFont.truetype('font/Aileron-Regular.otf', 24)
font28 = ImageFont.truetype('font/Aileron-Regular.otf', 28)
font144 = ImageFont.truetype('font/Aileron-Regular.otf', 144)
discord_color = ImageColor.getrgb('#7595FF')
discord_shaded = ImageColor.getrgb('#98aae6')
discord_complementary = ImageColor.getrgb('#ffb375')

ui = Image.open('images/Koyomi_Background_Template.png')


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
                'owned_badges': {'discord': 1},
                'selected_badge': 'discord',
                'waifu': 'None',
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

    def get_owned_badges(self):
        return json.loads(self.get_field('owned_badges'))

    def get_selected_badge(self):
        return self.get_field('selected_badge')

    def get_waifu(self):
        return self.get_field('waifu')

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

    def check_coins(self, coins: int):
        if self.get_coins() >= coins:
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
        if coins <= 0:
            return
        if self.check_coins(coins) and koyomi_user:
            self.use_coins(coins)
            koyomi_user.add_coins(coins)

    def poke(self, koyomi_user):
        if koyomi_user and self.check_cooldown('poke_cd', 3600):
            self.inc_field('pokes_given', 1)
            self.add_xp(300)
            koyomi_user.inc_field('pokes_received', 1)
            koyomi_user.add_coins(300)
            self.set_cooldown('poke_cd')
            return True
        return False

    def set_waifu(self):
        """ Set Waifu """
        pass

    def set_description(self):
        """ Set description. """
        pass

    def view_shop(self):
        """ To view the badge shop"""
        pass

    def view_inventory(self):
        """ A way to see all the owned items. """
        pass

    def select_badge(self):
        """ Select the badge. """
        pass

    def text_at_angle(self, text, angle, font):

        txt = Image.new('L', (500, 50))
        d = ImageDraw.Draw(txt)
        d.text((0,0), text, font=font, fill=255)
        txt=txt.rotate(angle, Image.BICUBIC, expand=1)
        return txt

    async def get_profile(self, avatar_file, user):
        avatar_file = io.BytesIO(avatar_file)
        user_avatar = Image.open(avatar_file)
        user_avatar = user_avatar.resize((256, 256), Image.LANCZOS)

        background = Image.open('images/' + random.choice(background_imgs))
        background = background.resize((1024, 640), Image.LANCZOS)


        badge = Image.open('images/examplebadge.png')


        final = Image.new('RGBA', (1024, 640))
        pokes_r = self.text_at_angle('Pokes Received', 45, font24)
        pokes_g = self.text_at_angle('Pokes Given', -45, font24)

        final.paste(background)
        final.paste(user_avatar, (90, 101))
        final.paste(ui, (0, 0), ui)
        final.paste(ImageOps.colorize(pokes_r, (0, 0, 0), discord_color), (455, 255), pokes_r)
        final.paste(ImageOps.colorize(pokes_g, (0, 0, 0), discord_color), (625, 500), pokes_g)
        draw = ImageDraw.Draw(final)
        draw.text((350,250), user.display_name + self.get_name()[-5:], font=font28, fill=(69,69,69))
        draw.text((80,2), 'Lv. ' + str(self.get_level()), font=font28, fill=discord_complementary)
        draw.text((350,290), 'ID: ' + str(user.id), font=font12, fill=discord_color)
        draw.text((960,22), '{:02d}%'.format(self.get_percent()), font=font24, fill=discord_complementary)
        draw.text((520,600), '{}'.format(self.get_pokes_received()).rjust(6), font=font24, fill=(117, 218, 255))
        draw.text((620,600), '{}'.format(self.get_pokes_given()).rjust(6), font=font24, fill=(117, 218, 255))
        draw.text((85,420), 'Aragis : ' + '{}'.format(self.get_coins()).rjust(20), font=font28, fill=(154, 117, 255))
        draw.text((85,480), 'Waifu : ' + '-insert waifu here-'.rjust(25), font=font28, fill=(154, 117, 255))

        top_side = (int(self.get_percent() * 6.6) + 365,  0)
        bottom_side = (top_side[0] - 15, 15)
        draw.polygon([(350, 15), (365, 0), top_side, bottom_side], discord_shaded)
        # for x in range(wa20):
        #    draw.text((random.randint(1, 600), random.randint(1, 1000)), 'TRIGGERED', font=font144, fill=(255,0,0))

        final.paste(badge, (5, 0), badge)
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
            koyomiuser.add_xp(random.randint(1, 5))

        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('avatar')

    @commands.command()
    async def give(self, ctx, *, args):
        try:
            args = args.split(' ', 1)
            coins = int(args[0])
            name = args[1]
            user = self.getuser(ctx, name)
            if not user or user == ctx.author:
                return
            sender_koyomi_user = self.get_koyomi_user(ctx.author)
            recipient_koyomi_user = self.get_koyomi_user(user)

            if coins <= 0 or not sender_koyomi_user.check_coins(coins):
                await ctx.send('Not Enough Aragis')

            sender_koyomi_user.give_coins(coins, recipient_koyomi_user)
            await ctx.send('{0} gave {1} Aragis to {2}'.format(ctx.author.mention, coins, user.mention))
        except:
            await ctx.send('Wrong Syntax. {}give [coins] [user]'.format(self.bot.command_prefix))

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
        em.add_field(name="Pokes Given", value=koyomi_user.get_pokes_given())
        em.add_field(name="Pokes Received", value=koyomi_user.get_pokes_received())
        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('profile')

    @commands.command()
    async def poke(self, ctx, *, name: str=None):
        user = self.getuser(ctx, name)
        if not user or user == ctx.author:
            return
        to_koyomi_user = self.get_koyomi_user(user)
        koyomi_user = self.get_koyomi_user(ctx.author)
        if koyomi_user.poke(to_koyomi_user):
            await ctx.send('{} poked {}!'.format(ctx.author.mention, user.mention))
        else:
            await ctx.send('You already used your poke! (Pokes have 1 hour cooldown.)')

    @commands.command(hidden=True)
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
