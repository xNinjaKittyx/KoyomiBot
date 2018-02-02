
import random

from discord.ext import commands

from utility import discordembed as dmbd
from utility.redis import redis_pool


class Slots:

    def __init__(self, bot):
        self.bot = bot
        self.emojis = [
            ':100:',
            ':snake:',
            ':watermelon:',
            ':cherries:'
        ]
        if not self.bot.loop.run_until_complete(
                redis_pool.get('jackpot')):
            self.bot.loop.run_until_complete(
                redis_pool.set('jackpot', 0))

    @commands.cooldown(3, 60, commands.BucketType.user)
    @commands.command()
    async def slots(self, ctx, bet: int):
        """ Bet your Aragis for more Aragis. """
        if len(self.emojis) != 6:
            for x in self.bot.emojis:
                if x.name == 'FeelsBadMan':
                    self.emojis.append(x)
                    break

            for x in self.bot.emojis:
                if x.name == 'thonking':
                    self.emojis.append(x)
                    break
        user = await self.bot.cogs['Profile'].get_koyomi_user(ctx.author)
        if await user.get_coins() >= bet >= 0:
            slot1 = random.randint(0, 5)
            slot2 = random.randint(0, 5)
            slot3 = random.randint(0, 5)
            result = set([slot1, slot2, slot3])
            final = '||{0}|{1}|{2}||'.format(
                self.emojis[slot1],
                self.emojis[slot2],
                self.emojis[slot3]
            )
            final += '\nPlaced {} into the machine\n'.format(bet)
            if len(result) == 3:
                final += '\nBetter Luck Next Time.'
                await redis_pool.incrby('jackpot', max(int(bet * .5), 1))
                await user.use_coins(bet)
            elif len(result) == 2:
                final += '\nSo close... You won {} Aragis'.format(bet * 2)
                await user.set_coins(await user.get_coins() + bet)
            elif len(result) == 1:
                jack = int(await redis_pool.get('jackpot').decode('utf-8'))
                final += '\nJACKPOT!! You won {} Aragis'.format(bet * 4 + jack)
                await user.set_coins(await user.get_coins() + (bet * 3 + jack))
                await redis_pool.set('jackpot', 0)

            em = dmbd.newembed(ctx.author, 'SLOT MACHINE', final)
            await ctx.send(embed=em)

    @commands.command()
    async def slotpot(self, ctx):
        """ The Current JackPot for Slots."""
        await ctx.send('The Current Jackpot for Slots is ' + await redis_pool.get('jackpot').decode('utf-8') + ' Aragis.')

    @slots.error
    async def on_slot_error(self, ctx, error):
        if type(error) == commands.CommandOnCooldown:
            await ctx.send('Try again after {} seconds.'.format(int(error.retry_after)))
        print(error)


def setup(bot):
    bot.add_cog(Slots(bot))
