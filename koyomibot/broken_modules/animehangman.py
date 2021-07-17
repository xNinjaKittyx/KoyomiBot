import random

from discord.ext import commands

from koyomibot.utility import discordembed as dmbd
from koyomibot.utility.redis import redis_pool


class Animehangman:
    def __init__(self, bot):
        self.bot = bot
        self.anilistid = self.bot.config["AnilistID"]
        self.anilistsecret = self.bot.config["AnilistSecret"]
        if not self.anilistid or not self.anilistsecret:
            print("ID or Secret is missing for AniList")
            raise ImportError
        self.max = 90248
        self.bot.loop.run_until_complete(redis_pool.delete("achminst"))

    async def refreshtoken(self):
        if await redis_pool.exists("AnilistToken"):
            return
        else:
            async with self.bot.session.post(
                "https://anilist.co/api/auth/access_token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.anilistid,
                    "client_secret": self.anilistsecret,
                },
            ) as r:
                if r.status != 200:
                    return
                results = await r.json()
                await redis_pool.setex("AnilistToken", 3600, results["access_token"])

    async def display(self, ctx, currentboard, guess, misses, picture, win=0):
        subtitle = "Where you test your weeb level!"
        em = dmbd.newembed(ctx.author, "Anime Hangman!", subtitle)
        em.set_image(url=picture)

        em.add_field(name="Word", value="`" + currentboard.title() + "`", inline=False)
        if misses:
            em.add_field(name="Guess", value=guess)
            em.add_field(name="Misses", value=" ".join(misses))
        if not (len(misses) == 6 or win == 1):
            em.add_field(
                name="How to Play",
                value=(
                    "Use " + self.bot.command_prefix + "guess [x] to guess the next letter\n"
                    "Type " + self.bot.command_prefix + "guess quit to exit\n"
                ),
                inline=False,
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
        return await ctx.send(embed=em)

    async def displayanswer(self, ctx, char):
        try:
            anime = char["anime"][0]
        except IndexError:
            anime = char["anime"]
        subtitle = anime["title_japanese"]
        url = "https://anilist.co/anime/" + str(anime["id"])
        em = dmbd.newembed(ctx.author, "Here's the answer!", subtitle, url)
        em.set_image(url=anime["image_url_lge"])
        em.add_field(name=anime["title_romaji"], value=anime["title_english"])
        em.add_field(name="Type", value=anime["type"])
        em.add_field(name="Rating", value=anime["average_score"])
        try:
            name_last = str(char["name_last"])
        except Exception:
            name_last = ""
        em.add_field(name=char["name_japanese"], value=char["name_first"] + " " + name_last)

        await ctx.send(embed=em)

    async def getchar(self):
        char = None
        while char is None:
            async with self.bot.session.get(
                "https://anilist.co/api/character/"
                + str(random.randint(1, self.max))
                + "/page?access_token="
                + await redis_pool.get("AnilistToken").decode("utf-8")
            ) as r:
                if r.status != 200:
                    self.bot.logger.warning("ANIME CHARACTER RETURNING 404")
                    continue
                tempchar = await r.json()

                self.bot.logger.debug(tempchar["id"])
            default = "https://cdn.anilist.co/img/dir/character/reg/default.jpg"
            if tempchar["anime"] == [] or tempchar["image_url_lge"] == default:
                continue
            char = tempchar
        return char

    @commands.command(no_pm=True)
    async def achm(self, ctx):
        """Play Anime Character Hangman!"""
        await self.bot.cogs["Wordcount"].cmdused("achm")
        if await redis_pool.exists("achminst"):
            for instance in await redis_pool.lrange("achminst", 0, -1):
                if ctx.channel.id == int(instance.decode("utf-8")):
                    await ctx.send("There's already a game running!")
                    return

        await self.refreshtoken()

        char = await self.getchar()

        answer = char["name_first"].lower()
        currentboard = "_" * len(char["name_first"])
        if char["name_last"]:
            answer += " " + char["name_last"].lower()
            currentboard += " " + "_" * len(char["name_last"])
        misses = []
        guess = "FirstDisplay"
        picture = char["image_url_lge"]
        prev_message = await self.display(ctx, currentboard, guess, misses, picture)
        await redis_pool.rpush("achminst", ctx.channel.id)
        while True:

            def check(msg):
                return msg.content.startswith(self.bot.command_prefix + "guess") and msg.channel == ctx.channel

            msg = await self.bot.wait_for("message", check=check)
            await prev_message.delete()
            pref_length = len(self.bot.command_prefix) + 5
            guess = msg.content[pref_length:].strip().lower()

            # checking the guess, and filling out the hangman as follows

            if len(guess) < 1:
                await ctx.send("You need to give me a letter!")
            elif guess == "quit":
                await ctx.send("You Ragequit? What a loser.")
                for _ in range(6 - len(misses)):
                    misses.append(".")
                await self.display(ctx, currentboard, guess, misses, picture, 0)
                break
            elif len(guess) > 1:
                if len(answer) < len(guess):
                    await ctx.send("Your guess is too long. Try Again.")
                    guess = ";^)"
                elif guess == answer:
                    currentboard = answer
                else:
                    misses.append(guess)
            elif guess in misses:
                await ctx.send("You've already used that letter!")
            elif guess in answer:
                for number, value in enumerate(answer):
                    if value == guess:
                        currentboard = currentboard[:number] + value + currentboard[number + 1 :]
            else:
                misses.append(guess)

            # checking if the answer has been done, or if the game has finished.

            if currentboard == answer:
                await self.display(ctx, currentboard, guess, misses, picture, 1)
                break
            elif len(misses) >= 6:
                await self.display(ctx, currentboard, guess, misses, picture, 0)
                break
            else:
                prev_message = await self.display(ctx, currentboard, guess, misses, picture, 0)

        await self.displayanswer(ctx, char)
        await redis_pool.lrem("achminst", 1, ctx.channel.id)
        return


def setup(bot):
    bot.add_cog(Animehangman(bot))
