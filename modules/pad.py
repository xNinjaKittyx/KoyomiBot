import asyncio
import logging
from operator import itemgetter

import discord
import simplefuzzyset as fuzzyset
import rapidjson

from discord.ext import commands

import utility.discordembed as dmbd
from main import MyClient


log = logging.getLogger(__name__)


class PAD(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot
        self.bot.loop.create_task(self.refresh())

    async def refresh(self) -> None:
        one_day = 24 * 60 * 60
        while True:
            mons = await self.bot.db.redis.get("pad:monsters")
            if not mons:
                async with self.bot.session.get("https://www.padherder.com/api/monsters/") as r:
                    if r.status != 200:
                        log.warning("/api/monsters/ is down")
                        self.monsters = []
                    else:
                        self.monsters = await r.json()
                        await self.bot.db.redis.set(
                            "pad:monsters", rapidjson.dumps(self.monsters), expire=one_day,
                        )
            else:
                self.monsters = rapidjson.loads(mons)

            log.info("Refreshed PAD Monsters")
            awake = await self.bot.db.redis.get("pad:awakenings")
            if not awake:
                async with self.bot.session.get("https://www.padherder.com/api/awakenings/") as r:
                    if r.status != 200:
                        log.warning("/api/awakenings/ is down")
                        self.awakenings = []
                    else:
                        self.awakenings = await r.json()
                        await self.bot.db.redis.set(
                            "pad:awakenings", rapidjson.dumps(self.awakenings), expire=one_day,
                        )
            else:
                self.awakenings = rapidjson.loads(awake)
            log.info("Refreshed PAD Awakenings")
            await asyncio.sleep(3600)

    async def getawaken(self, skills: list) -> str:
        result = []
        if not skills:
            return "None"
        for x in skills:
            result.append(self.awakenings[x - 1]["name"])
        return "\n".join(result)

    @staticmethod
    def gettype(type1: int, type2: int = None, type3: int = None) -> str:
        types = [
            "Evo Material",
            "Balanced",
            "Physical",
            "Healer",
            "Dragon",
            "God",
            "Attacker",
            "Devil",
            "Machine",
            "",
            "",
            "",
            "",
            "",
            "Enhance Material",
        ]
        if type2 is None:
            return types[type1]
        elif type3 is None:
            return "{0}/{1}".format(types[type1], types[type2])
        else:
            return "/".join([types[type1], types[type2], types[type3]])

    async def monster_embed(self, mon: dict, author: str) -> discord.Embed:
        title = mon["name"]
        description = mon["name_jp"] + "\n" + "*" * mon["rarity"]
        url = "http://puzzledragonx.com/en/monster.asp?n=" + str(mon["id"])
        em = dmbd.newembed(author, title, description, url)
        em.set_thumbnail(url="https://www.padherder.com" + mon["image60_href"])
        em.add_field(name="Type", value=self.gettype(mon["type"], mon["type2"], mon["type3"]))
        em.add_field(name="Team Cost", value=mon["team_cost"])
        em.add_field(name="MaxLv", value="{} ({}xp)".format(mon["max_level"], mon["xp_curve"]))
        em.add_field(name="HP", value="[{}][{}]".format(mon["hp_min"], mon["hp_max"]))
        em.add_field(name="ATK", value="[{}][{}]".format(mon["atk_min"], mon["atk_max"]))
        em.add_field(name="RCV", value="[{}][{}]".format(mon["rcv_min"], mon["rcv_max"]))
        em.add_field(name="Leader Skill", value=mon["leader_skill"])
        em.add_field(name="Active Skill", value=mon["active_skill"])
        em.add_field(name="MP Sell Price", value=mon["monster_points"])
        em.add_field(
            name="Awakenings", value=await self.getawaken(mon["awoken_skills"]), inline=False,
        )

        return em

    @commands.command()
    async def pad(self, ctx: commands.Context, *, arg: str) -> None:
        """ Searches a PAD monster"""
        if not self.awakenings or not self.monsters:
            log.error("PAD awakenings/monsters not exist.")
            return
        author = ctx.author
        try:
            # If Arg is a number.
            index = int(arg)
            monster = self.monsters[index]
            await ctx.send(embed=await self.monster_embed(monster, author))
            return
        except ValueError:
            if len(arg) < 4:
                await ctx.send("Please use more than 3 letters")
                return
            arg = arg.lower()
        except IndexError:
            await ctx.send("ID is not valid.")
            return

        fuzzy = fuzzyset.FuzzySet()
        fuzzy.add(arg)
        results = []
        # First check if str is too short...
        for (n, m) in enumerate(self.monsters):

            fuzzy_value = fuzzy.get(m["name"])
            fuzzy_value_jp = fuzzy.get(m["name_jp"])

            if fuzzy_value is not None and fuzzy_value_jp is not None:
                if fuzzy_value[0][0] > fuzzy_value_jp[0][0]:
                    results.append((n, fuzzy_value[0][0], "name"))
                else:
                    results.append((n, fuzzy_value_jp[0][0], "name_jp"))
            elif fuzzy_value is not None:
                results.append((n, fuzzy_value[0][0], "name"))
            elif fuzzy_value_jp is not None:
                results.append((n, fuzzy_value_jp[0][0], "name_jp"))

        sorted_results = sorted(results, key=itemgetter(1), reverse=True)

        if len(sorted_results) > 1:
            possible_results = [
                "{}: {}  {}".format(index, self.monsters[index][name_type], fuzzy)
                for i, (index, fuzzy, name_type) in zip(range(20), sorted_results)
            ]
            confused = await ctx.send("Which one did you mean? Respond with number.\n" + "\n".join(possible_results))

            def check(msg):
                if msg.content.isdigit():
                    return (
                        msg.author == ctx.author
                        and msg.channel == ctx.channel
                        and 0 <= int(msg.content) < len(self.monsters)
                    )

            try:
                determine = await self.bot.wait_for("message", check=check, timeout=10)
            except TimeoutError:
                return
            finally:
                await confused.delete()
            if determine is None:
                return
            else:
                await ctx.send(embed=await self.monster_embed(self.monsters[int(determine.content)], author))
        elif len(results) == 1:
            await ctx.send(embed=await self.monster_embed(self.monsters[sorted_results[0][0]], author))
        else:
            await ctx.send("No Monster Found")


def setup(bot: MyClient) -> None:
    bot.add_cog(PAD(bot))
