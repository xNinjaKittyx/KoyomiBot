
import json
import io
import random
import time

from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageColor

import aioredis


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
font22 = ImageFont.truetype('font/Aileron-Regular.otf', 22)
font24 = ImageFont.truetype('font/Aileron-Regular.otf', 24)
font28 = ImageFont.truetype('font/Aileron-Regular.otf', 28)
font144 = ImageFont.truetype('font/Aileron-Regular.otf', 144)
discord_color = ImageColor.getrgb('#7595FF')
discord_shaded = ImageColor.getrgb('#98aae6')
discord_complementary = ImageColor.getrgb('#ffb375')

ui = Image.open('images/Koyomi_Background_Template.png')


class KoyomiUser:

    def __init__(self, author, loop):
        self.loop = loop
        self.redis_pool = self.loop.run_until_complete(
            aioredis.create_redis_pool(('localhost', 6379), db=1))
        self.author_id = author.id
        if not self.loop.run_until_complete(self.redis_pool.exists(author.id)):
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
                'description': 'Kamimashita',
                'waifu': 'None',
            }
            self.loop.run_until_complete(self.redis_pool.hmset(author.id, default_profile))
        else:
            self.loop.run_until_complete(
                self.redis_pool.hset(author.id, 'name', author.name + "#" + author.discriminator))

    # Generic functions used often for redis.
    async def get_field(self, key):
        return await self.redis_pool.hget(self.author_id, key).decode('utf-8')

    async def set_field(self, key, value):
        return await self.redis_pool.hset(self.author_id, key, value)

    async def inc_field(self, key, amount):
        return await self.redis_pool.hincrby(self.author_id, key, amount)

    # Cooldown commands.
    async def get_cooldown(self, cooldown_type):
        return int(await self.get_field(cooldown_type))

    async def set_cooldown(self, cooldown_type):
        await self.redis_pool.hset(self.author_id, cooldown_type, int(time.time()))

    async def check_cooldown(self, cooldown_type, seconds):
        if int(time.time()) - await self.get_cooldown(cooldown_type) > seconds:
            return True
        return False

    async def remaining_cooldown(self, cooldown_type):
        return int(time.time() - await self.get_cooldown(cooldown_type))

    # xp commands.
    @property
    def xp(self):
        return int(self.loop.run_until_complete(self.get_field('xp')))

    @xp.setter
    def xp(self, exp: int):
        if exp < 0:
            return
        self.loop.run_until_complete(
            self.set_field('xp', exp)
        )
        if self.xp > self.get_required_xp():
            # the player leveled up!
            self.coins += 100
            self.level += 1
            self.set_field('xp', 0)

    # name getter and setter.
    @property
    def name(self):
        return str(self.loop.run_until_complete(
            self.get_field('name')
        ))

    @name.setter
    def name(self, value):
        self.loop.run_until_complete(
            self.set_field('name', value)
        )

    # Coins get, add, use
    @property
    def coins(self):
        return int(self.loop.run_until_complete(
            self.get_field('coins'))
        )

    @coins.setter
    def coins(self, value):
        if value >= 0:
            self.loop.run_until_complete(
                self.set_field('coins', value)
            )
        else:
            return

    def use_coins(self, coins):
        if self.coins >= coins:
            self.coins -= coins
        else:
            raise NameError('Not Enough Minerals')

    def give_coins(self, coins: int, koyomi_user):
        if coins <= 0:
            return
        if koyomi_user:
            self.use_coins(coins)
            koyomi_user.coins += coins

    # Level getter and setter.
    @property
    def level(self):
        return int(self.loop.run_until_complete(
            self.get_field('level')))

    @level.setter
    def level(self, value):
        self.loop.run_until_complete(
            self.set_field('level', value)
        )

    # Find out how much xp is left.
    def get_required_xp(self):
        level_to_get = self.level + 1
        return int(100 + level_to_get ** 1.5)

    # Find out what % you're at.
    def get_percent(self):
        return int((self.xp / self.get_required_xp()) * 100)

    @property
    def pokes_given(self):
        return int(
            self.loop.run_until_complete(
                self.get_field('pokes_given'))
        )

    @pokes_given.setter
    def pokes_given(self, value):
        self.loop.run_until_complete(
            self.set_field('pokes_given', value)
        )

    @property
    def pokes_received(self):
        return int(
            self.loop.run_until_complete(
                self.get_field('pokes_received'))
        )

    @pokes_received.setter
    def pokes_received(self, value):
        self.loop.run_until_complete(
            self.set_field('pokes_received', value)
        )

    def get_owned_badges(self):
        return json.loads(
            self.loop.run_until_complete(
                self.get_field('owned_badges'))
        )

    @property
    def badge(self):
        return self.loop.run_until_complete(
            self.get_field('selected_badge')
        )

    @badge.setter
    def badge(self, value):
        self.loop.run_until_complete(
            self.set_field('selected_badge', value)
        )

    @property
    def description(self):
        return self.loop.run_until_complete(
            self.get_field("description")
        )

    @description.setter
    def description(self, value):
        self.loop.run_until_complete(
            self.set_field('description', value)
        )

    @property
    def waifu(self):
        return self.loop.run_until_complete(
            self.get_field('waifu')
        )

    @waifu.setter
    def waifu(self, value):
        self.loop.run_until_complete(
            self.set_field('waifu', value)
        )

    async def poke(self, koyomi_user):
        if koyomi_user and await self.check_cooldown('poke_cd', 3600):
            self.pokes_given += 1
            self.xp += 300
            koyomi_user.pokes_received += 1
            koyomi_user.coins += 300
            await self.set_cooldown('poke_cd')
            return True
        return False

    def view_shop(self):
        """ To view the badge shop"""
        pass

    def view_inventory(self):
        """ A way to see all the owned items. """
        pass

    def text_at_angle(self, text, angle, font):
        txt = Image.new('L', (500, 50))
        d = ImageDraw.Draw(txt)
        d.text((0, 0), text, font=font, fill=255)
        txt = txt.rotate(angle, Image.BICUBIC, expand=1)
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
        draw.text((350, 250), user.display_name + self.name[-5:], font=font28, fill=(69,69,69))
        draw.text((80, 2), 'Lv. ' + str(self.level), font=font28, fill=discord_complementary)
        draw.text((350, 290), self.description.center(25), font=font24, fill=discord_color)
        draw.text((90, 360), 'ID: ' + str(user.id), font=font22, fill=discord_color)
        draw.text((960, 22), '{:02d}%'.format(self.get_percent()), font=font24, fill=discord_complementary)
        draw.text((520, 600), '{}'.format(self.pokes_received).rjust(6), font=font24, fill=(117, 218, 255))
        draw.text((620, 600), '{}'.format(self.pokes_given).rjust(6), font=font24, fill=(117, 218, 255))
        draw.text((85, 420), 'Aragis : ' + '{}'.format(self.coins).rjust(20), font=font28, fill=(154, 117, 255))
        draw.text((85, 480), 'Waifu : ' + self.waifu.rjust(18), font=font28, fill=(154, 117, 255))

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
