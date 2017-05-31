# -*- coding: utf8 -*-
from datetime import datetime
import random

from discord.ext import commands
from utility import discordembed as dmbd


class Animehangman:

    def __init__(self, bot):
        self.bot = bot
        self.anilistid = bot.redis_db.get('AnilistID').decode('utf-8')
        self.anilistsecret = bot.redis_db.get('AnilistSecret').decode('utf-8')
        if not self.anilistid or not self.anilistsecret:
            print('ID or Secret is missing for AniList')
            raise ImportError
        self.max = 90248
        self.access_token = None
        self.lastaccess = None
        self.firsttime = True
        self.currentboard = ""
        bot.redis_db.delete('achminst')

    async def getaccesstoken(self):
        async with self.bot.session.post(
            'https://anilist.co/api/auth/access_token', data={
                'grant_type': 'client_credentials',
                'client_id': self.anilistid,
                'client_secret': self.anilistsecret
            }
        ) as r:
            if r.status != 200:
                return
            results = await r.json()
            self.access_token = results['access_token']
            self.lastaccess = datetime.today()

    async def refreshtoken(self):
        if self.firsttime:
            self.firsttime = False
            await self.getaccesstoken()
        delta = (datetime.today() - self.lastaccess)
        if delta.seconds > 3600 or delta.days > 0:
            await self.getaccesstoken()

    async def display(self, guess, misses, author, picture, win=0):
        subtitle = "Where you test your weeb level!"
        em = dmbd.newembed(author, "Anime Hangman!", subtitle)
        em.set_image(url=picture)

        em.add_field(name="Word", value="`" + self.currentboard.title() + "`", inline=False)
        if misses != []:
            em.add_field(name="Guess", value=guess)
            em.add_field(name="Misses", value=' '.join(misses))
        if not (len(misses) == 6 or win == 1):
            em.add_field(
                name="How to Play",
                value=(
                    "Use " + self.bot.command_prefix +
                    "guess [x] to guess the next letter\n"
                    "Type " + self.bot.command_prefix +
                    "guess quit to exit\n"
                ),
                inline=False
            )

        if len(misses) == 0:
            em.set_thumbnail(url="https://goo.gl/FMUQrp")
        elif len(misses) == 1:
            em.set_thumbnail(url="https://goo.gl/fKvyTp")
        elif len(misses) == 2:
            em.set_thumbnail(url="https://goo.gl/dTVKVX")
        elif len(misses) == 3:
            em.set_thumbnail(url="https://goo.gl/BqiCFi")
        elif len(misses) == 4:
            em.set_thumbnail(url="https://goo.gl/XgytvK")
        elif len(misses) == 5:
            em.set_thumbnail(url="https://goo.gl/AevCAI")
        elif len(misses) == 6:
            em.set_thumbnail(url="https://goo.gl/8ymxqs")
            em.add_field(name="You Lose!", value="lul", inline=False)

        if win == 1:
            em.add_field(name="You Win!", value="You weeb...", inline=False)
        return await self.bot.say(embed=em)

    async def displayanswer(self, author, char):
        try:
            anime = char['anime'][0]
        except:
            anime = char['anime']
        subtitle = anime['title_japanese']
        url = "https://anilist.co/anime/" + str(anime['id'])
        em = dmbd.newembed(author, 'Here\'s the answer!', subtitle, url)
        em.set_image(url=anime['image_url_lge'])
        em.add_field(name=anime['title_romaji'], value=anime['title_english'])
        em.add_field(name="Type", value=anime['type'])
        em.add_field(name='Rating', value=anime['average_score'])
        xstr = lambda s: s or ""
        em.add_field(name=char['name_japanese'], value=char['name_first'] + " " + xstr(char['name_last']))

        await self.bot.say(embed=em)


    @commands.command(pass_context=True, no_pm=True)
    async def achm(self, ctx):
        """ Play Anime Character Hangman!"""
        if self.bot.redis_db.exists('achminst'):
            for instance in self.bot.redis_db.lrange('achminst', 0, -1):
                if ctx.message.channel.id == instance.decode('utf-8'):
                    await self.bot.say("There's already a game running!")
                    return

        await self.refreshtoken()

        char = None
        while char is None:
            async with self.bot.session.get(
                "https://anilist.co/api/character/" +
                str(random.randint(1, self.max)) +
                "/page?access_token=" +
                self.access_token
            ) as r:
                if r.status != 200:
                    print("ANIME CHARACTER RETURNING 404")
                    continue
                character = await r.json()

            print(character["id"])
            if character["anime"] == [] or character['image_url_lge'] == "https://cdn.anilist.co/img/dir/character/reg/default.jpg":
                continue
            char = character

        answer = char["name_first"].lower()
        self.currentboard = "_"*len(char["name_first"])
        if char["name_last"]:
            answer += " " + char["name_last"].lower()
            self.currentboard += " " + "_"*len(char["name_last"])
        misses = []
        guess = "FirstDisplay"
        picture = char["image_url_lge"]
        author = ctx.message.author
        prev_message = await self.display(guess, misses, author, picture)
        self.bot.redis_db.rpush('achminst', ctx.message.channel.id)
        while self.currentboard != answer or len(misses) < 6:

            def check(msg):
                return msg.content.startswith(self.bot.command_prefix + 'guess')

            msg = await self.bot.wait_for_message(
                channel=ctx.message.channel,
                check=check
                )
            await self.bot.delete_message(prev_message)
            author = msg.author
            pref_length = len(self.bot.command_prefix) + 5
            guess = msg.content[pref_length:].strip().lower()

            if len(guess) < 1:
                await self.bot.say("You need to give me a letter!")
            elif guess == 'quit':
                self.bot.redis_db.lrem('achminst', 1, ctx.message.channel.id)
                await self.bot.say("You Ragequit? What a loser.")
                for x in range(6 - len(misses)):
                    misses.append('.')
                await self.display(guess, misses, author, picture, 0)
                await self.displayanswer(author, char)
                return
            elif len(guess) > 1:
                if len(answer) < len(guess):
                    await self.bot.say("Your guess is too long. Try Again.")
                    guess = ";^)"
                elif guess == answer:
                    self.currentboard = answer
                else:
                    misses.append(guess)
            elif guess in misses:
                await self.bot.say("You've already used that letter!")
            elif guess in answer:
                for number, value in enumerate(answer):
                    if value == guess:
                        self.currentboard = self.currentboard[:number] + value + self.currentboard[number+1:]
            else:
                misses.append(guess)


            if self.currentboard == answer:
                await self.display(guess, misses, author, picture, 1)
                await self.displayanswer(author, char)
                self.bot.redis_db.lrem('achminst', 1, ctx.message.channel.id)
                return
            elif len(misses) >= 6:
                await self.display(guess, misses, author, picture, 0)
                await self.displayanswer(author, char)
                self.bot.redis_db.lrem('achminst', 1, ctx.message.channel.id)
                return
            else:
                prev_message = await self.display(guess, misses, author, picture, 0)

        self.bot.redis_db.lrem('achminst', 1, ctx.message.channel.id)
        return

def setup(bot):
    bot.add_cog(Animehangman(bot))
