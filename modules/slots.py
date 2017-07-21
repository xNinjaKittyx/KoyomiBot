
import random

from discord.ext import commands

from utility import discordembed as dmbd


class Slots:

    def __init__(self, bot):
        self.bot = bot
        self.emojis = [
            ':100:',
            ':snake:',
            ':watermelon:',
            ':cherries:'
        ]
        if not self.bot.redis_db.get('jackpot'):
            self.bot.redis_db.set('jackpot', 0)

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
                if x.name == 'thignkin':
                    self.emojis.append(x)
                    break
        user = self.bot.cogs['Profile'].get_koyomi_user(ctx.author)
        if user.coins >= bet >= 0:
            slot1 = random.randint(0, 5)
            slot2 = random.randint(0, 5)
            slot3 = random.randint(0, 5)
            result = set([slot1, slot2, slot3])
            final = '||{0}|{1}|{2}||'.format(
                self.emojis[slot1],
                self.emojis[slot2],
                self.emojis[slot3]
            )
            if len(result) == 3:
                final += '\nBetter Luck Next Time. You lost {} Aragis'.format(bet)
                self.bot.redis_db.incrby('jackpot', max(int(bet * .5), 1))
                user.use_coins(bet)
            elif len(result) == 2:
                final += '\nSo close... You won {} Aragis'.format(bet)
                user.coins += bet
            elif len(result) == 1:
                jack = int(self.bot.redis_db.get('jackpot').decode('utf-8'))
                final += '\nJACKPOT!! You won {} Aragis'.format(bet * 3 + jack)
                user.coins += bet * 3 + jack
                self.bot.redis_db.set('jackpot', 0)

            em = dmbd.newembed(ctx.author, 'SLOT MACHINE', final)
            await ctx.send(embed=em)

    @commands.command()
    async def slotpot(self, ctx):
        """ The Current JackPot for Slots."""
        await ctx.send('The Current Jackpot for Slots is ' + self.bot.redis_db.get('jackpot').decode('utf-8') + ' Aragis.')

    @slots.error
    async def on_slot_error(self, ctx, error):
        if type(error) == commands.CommandOnCooldown:
            await ctx.send('Try again after {} seconds.'.format(int(error.retry_after)))
        print(error)


def setup(bot):
    bot.add_cog(Slots(bot))
