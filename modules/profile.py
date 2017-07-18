
import random

import discord
from discord.ext import commands
import utility.discordembed as dmbd
from utility.koyomiuser import KoyomiUser



class Profile:

    def __init__(self, bot):
        self.bot = bot
        self.users = {} # userid: KoyomiUser
        self.XP_RATE = 1
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
            user.xp += random.randint(5, 20)
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

        if author != user or not user.bot:
            koyomiuser = self.get_koyomi_user(user)
            koyomiuser.xp += random.randint(1, 5)

        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('avatar')

    @commands.command()
    async def badge(self, ctx, *, arg):
        # TODO
        if arg is None:
            """ print list of owned badges"""
            pass
        else:
            """ Set badge to arg """
            pass

    @commands.command()
    async def description(self, ctx, *, desc=None):
        """Either display the description, or give a description for your profile."""

        koyomiuser = self.get_koyomi_user(ctx.author)
        if desc is None:
            await ctx.send(koyomiuser.desciption)
        else:
            if len(desc) > 25:
                await ctx.send('Description is too long.')
            else:
                koyomiuser.description = desc
                await ctx.message.add_reaction('✅')
                self.bot.cogs['Wordcount'].cmdcount('description')


    @commands.command()
    @commands.is_owner()
    async def sudogive(self, ctx, *, args):
        try:
            args = args.split(' ', 1)
            coins = int(args[0])
            name = args[1]
            user = self.getuser(ctx, name)
            if not user or user.bot:
                return
            recipient_koyomi_user = self.get_koyomi_user(user)

            recipient_koyomi_user.coins += coins
            await ctx.send('{0} sudogave {1} Aragis to {2}'.format(ctx.author.mention, coins, user.mention))
        except:
            await ctx.send('Wrong Syntax. {}give [coins] [user]'.format(self.bot.command_prefix))

    @sudogive.error
    async def on_not_owner_error(self, ctx, error):
        if type(error) == commands.NotOwner:
            self.bot.logger.warning('{} tried to use sudogive.. But failed :DD'.format(ctx.author))

    @commands.command()
    async def give(self, ctx, *, args):
        try:
            args = args.split(' ', 1)
            coins = int(args[0])
            name = args[1]
            user = self.getuser(ctx, name)
            if not user or user == ctx.author or user.bot:
                return
            sender_koyomi_user = self.get_koyomi_user(ctx.author)
            recipient_koyomi_user = self.get_koyomi_user(user)

            if coins <= 0 or sender_koyomi_user.coins < coins:
                await ctx.send('Not Enough Aragis')

            sender_koyomi_user.give_coins(coins, recipient_koyomi_user)
            await ctx.send('{0} gave {1} Aragis to {2}'.format(ctx.author.mention, coins, user.mention))
            self.bot.cogs['Wordcount'].cmdcount('give')
        except:
            await ctx.send('Wrong Syntax. {}give [coins] [user]'.format(self.bot.command_prefix))

    @commands.command()
    async def profile(self, ctx, *,  name: str=None):
        """ Display Profile :o """

        user = self.getuser(ctx, name)
        if not user:
            return

        author = ctx.author
        userfull = user.name + '#' + user.discriminator
        em = dmbd.newembed(author, userfull, u=user.avatar_url)
        em.set_image(url=user.avatar_url)

        em.add_field(name='Username', value=userfull)
        em.add_field(name='UserID', value=user.id)
        if user.bot:
            em.add_field(name='Im a', value='bot keke')
            await ctx.send(embed=em)
            self.bot.cogs['Wordcount'].cmdcount('profile')
            return

        koyomi_user = self.get_koyomi_user(user)
        percent = koyomi_user.get_percent()

        em.add_field(name="Lv. " + str(koyomi_user.level), value='{}%'.format(percent))
        em.add_field(name="Bank", value='{} Aragis'.format(koyomi_user.coins))
        em.add_field(name="Pokes Given", value=koyomi_user.pokes_given)
        em.add_field(name="Pokes Received", value=koyomi_user.pokes_received)
        await ctx.send(embed=em)
        self.bot.cogs['Wordcount'].cmdcount('profile')

    @commands.command()
    async def poke(self, ctx, *, name: str=None):
        user = self.getuser(ctx, name)
        if not user or user == ctx.author or user.bot:
            return
        to_koyomi_user = self.get_koyomi_user(user)
        koyomi_user = self.get_koyomi_user(ctx.author)
        if koyomi_user.poke(to_koyomi_user):
            await ctx.send('{} poked {}!'.format(ctx.author.mention, user.mention))
            self.bot.cogs['Wordcount'].cmdcount('poke')
        else:
            await ctx.send('You already used your poke! ({} seconds cooldown)'.format(3600 - koyomi_user.remaining_cooldown('poke_cd')))


    @commands.command()
    async def waifu(self, ctx, *, arg=None):
        """ Set your waifu lol..."""

        koyomiuser = self.get_koyomi_user(ctx.author)
        if arg is None:
            await ctx.send(koyomiuser.waifu)
        else:
            if len(arg) > 18:
                await ctx.send('Waifu\'s name is too long.')
            else:
                koyomiuser.waifu = arg
                await ctx.message.add_reaction('✅')

                self.bot.cogs['Wordcount'].cmdcount('waifu')

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
