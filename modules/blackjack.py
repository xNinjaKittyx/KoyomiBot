
import random

from discord.ext import commands


class Card:
    def __init__(self, value: int, color: str):
        self.value = value
        self.color = color
        self._values = [None, "A", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K"]

    def __eq__(self, other):
        if self.value == other.value and self.color == other.color:
            return True
        return False

    def __str__(self):
        return "{} of {}".format(self._values(self.value), self.color)


class Deck:
    suits = ['hearts', 'diamonds', 'spades', 'clubs']

    def __init__(self):
        self.current = [Card(value, suit) for value in range(1, 14) for suit in self.suits]
        self.random = random.Random()

    def shuffle(self):
        self.random.shuffle(self.current)

    def deal_card(self):
        return self.current.pop()

    def remove_card(self, card):
        if card in self.current:
            self.current.remove(card)
            return True
        else:
            return False

    def add_card(self, card):
        if card in self.current:
            return False
        self.current.add(card)


class BlackJack:
    players = {
        # player_id
        # [Deck (set()), dealer_hand, player_hand]
    }

    def __init__(self, bot):
        self.bot = bot

    def check_blackjack(self, hand):
        if hand[0].value == 1:
            if hand[1].value >= 10:
                return True
        elif hand[1].value == 1:
            if hand[0].value >= 10:
                return True
        return False

    def get_score(self, hand):
        ace_count = 0
        total_value = 0
        for card in hand:
            if card.value >= 10:
                total_value += 10
            elif card.value == 1:
                ace_count += 1
                total_value += 11
            else:
                total_value += card.value

        if total_value > 21 and ace_count > 0:
            for _ in range(ace_count):
                total_value -= 10
                if total_value < 21:
                    return total_value
        return total_value

    @commands.command()
    async def blackjack(self, ctx, *, bet: int=0):

        # First check if game already in session.
        if ctx.author.id in self.players:
            output = []
            for card in self.players[ctx.author.id]['player_hand']:
                output.append(str(card))
            await ctx.send(
                "{}\n".format(ctx.author.mention) +
                "You already have a game in session." +
                "You currently have {}".format(", ".join(output)))
            return

        # Next check if user has enough money for his bet
        if not bet:
            await ctx.send(
                "{}\n".format(ctx.author.mention) +
                'It costs money to play blackjack you know...\nUsage: blackjack [bet]')
            return

        if bet < 10:
            await ctx.send(
                "{}\n".format(ctx.author.mention) +
                "You can't possibly be that cheap dude.")
            return

        koyomi_user = await self.bot.cogs['Profile'].get_koyomi_user(ctx.author)
        if await koyomi_user.get_coins() >= bet >= 10:
            await ctx.send('You put {} Aragis on the table.'.format(bet))
            await koyomi_user.use_coins(bet)
        else:
            await ctx.send(
                "{}\n".format(ctx.author.mention) +
                "You don't have enough money.")
            return

        # First shuffle some cards
        # Each player, you need to keep track of several things
        # 1) The Deck they have
        # 2) The hand they have
        # 3) The hend that the dealer has
        newdeck = Deck()
        newdeck.shuffle()
        player_hand = []
        dealer_hand = []

        for _ in range(2):
            player_hand.append(
                newdeck.deal_card()
            )
            dealer_hand.append(
                newdeck.deal_card()
            )

        player_score = self.get_score(player_hand)
        dealer_score = self.get_score(dealer_hand)

        if player_score == 21:
            if dealer_score == 21:
                await ctx.send(
                    "{}\n".format(ctx.author.mention) +
                    "Both players got blackjack. Got your money back!"
                )
                await koyomi_user.set_coins(await koyomi_user.get_coins() + bet)
                return
            else:
                await ctx.send(
                    "{}\n".format(ctx.author.mention) +
                    "\nYou got {} and {} ".format(*player_hand) +
                    "You got blackjack! Congrats!"
                )
                await koyomi_user.set_coins(await koyomi_user.get_coins() + bet * 2)
                return
        elif dealer_score == 21:
            await ctx.send(
                "{}\n".format(ctx.author.mention) +
                "Dealer got blackjack. You lose."
                )
            return
        else:
            await ctx.send(
                "{}".format(ctx.author.mention) +
                "\nYou got {} and {} ".format(*player_hand) +
                "\nDealer face-up Card: {}".format(dealer_hand[0]) +
                "\nYou can either >jhit, >jstand, or >jsurrender")

        self.players[ctx.author.id] = {
            'koyomi_user': koyomi_user,
            'bet': bet,
            'deck': newdeck,
            'player_hand': player_hand,
            'dealer_hand': dealer_hand
        }

    @commands.command()
    async def jhit(self, ctx):
        if ctx.author.id not in self.players:
            await ctx.send("No BlackJack Game in Session")
            return
        self.players[ctx.author.id]['player_hand'].append(
            self.players[ctx.author.id]['deck'].deal_card()
        )

        output = []
        for card in self.players[ctx.author.id]['player_hand']:
            output.append(str(card))

        player_score = self.get_score(self.players[ctx.author.id]['player_hand'])
        if player_score > 21:
            del self.players[ctx.author.id]
            await ctx.send(
                "{}\n".format(ctx.author.mention) +
                "You BUSTED. You had {}.\n".format(", ".join(output)) +
                "Better luck next time.")
        else:
            await ctx.send(
                "{}\n".format(ctx.author.mention) +
                "You HIT. You have {}.\n".format(", ".join(output))
            )

    @commands.command()
    async def jstand(self, ctx):
        output = []
        if ctx.author.id not in self.players:
            await ctx.send("No BlackJack Game in Session")
            return

        bet = self.players[ctx.author.id]['bet']

        player_hand_output = []
        for card in self.players[ctx.author.id]['player_hand']:
            player_hand_output.append(str(card))

        output.append("You have: " + ", ".join(player_hand_output))

        player_score = self.get_score(self.players[ctx.author.id]['player_hand'])
        output.append("\nYour score is {}.".format(player_score))

        while self.get_score(self.players[ctx.author.id]['dealer_hand']) < 17:
            card = self.players[ctx.author.id]['deck'].deal_card()
            self.players[ctx.author.id]['dealer_hand'].append(
                card
            )
            output.append("\nDealer draws {}".format(card))

        dealer_hand_output = []
        for card in self.players[ctx.author.id]['dealer_hand']:
            dealer_hand_output.append(str(card))

        output.append("\nDealer has: " + ", ".join(dealer_hand_output))
        dealer_score = self.get_score(self.players[ctx.author.id]['dealer_hand'])
        output.append('\nDealer score is {}'.format(dealer_score))
        if dealer_score > 21:
            koyomi_user = await self.bot.cogs['Profile'].get_koyomi_user(ctx.author)
            output.append('\nDealer busted. You won {} Aragis!'.format(
                bet * 2))
            await koyomi_user.set_coins(await koyomi_user.get_coins() + bet * 2)

        else:
            if dealer_score >= player_score:
                # If Player Loses
                output.append('\nYou lost!. Better luck next time.')
            else:
                # If player wins
                koyomi_user = await self.bot.cogs['Profile'].get_koyomi_user(ctx.author)
                output.append('\nYou Won! You won {} Aragis'.format(
                    bet * 2
                ))
                await koyomi_user.set_coins(await koyomi_user.get_coins() + bet * 2)

        del self.players[ctx.author.id]
        await ctx.send(
            "{}\n".format(ctx.author.mention) +
            ' '.join(output))

    @commands.command()
    async def jsurrender(self, ctx):
        if ctx.author.id in self.players:
            await ctx.send(
                "{}\n".format(ctx.author.mention) +
                "You've decided to surrender your hand. You will get half your bet back."
            )
            koyomi_user = self.players[ctx.author.id]['koyomi_user']
            await koyomi_user.set_coins(
                await koyomi_user.get_coins() + (
                    self.players[ctx.author.id]['bet'] // 2))
            del self.players[ctx.author.id]
        else:
            await ctx.send(
                'No BlackJack Game in Session'
            )


def setup(bot):
    """ Setup Blackjack.py"""
    bot.add_cog(BlackJack(bot))
