
import asyncio
import logging
from operator import itemgetter

import discord
import fuzzyset
import rapidjson

from discord.ext import commands

import utility.discordembed as dmbd
from main import MyClient


log = logging.getLogger(__name__)


class PAD(commands.Cog):
    def __init__(self, bot: MyClient):
        self.bot = bot

    async def refresh(self):
        one_day = 24 * 60 * 60
        while True:
            self.monsters = await self.bot.db.redis.get('pad:monsters')
            if not self.monsters:
                async with self.bot.session.get('https://www.padherder.com/api/monsters/') as r:
                    if r.status != 200:
                        log.warning('/api/monsters/ is down')
                    else:
                        self.monsters = await r.json()
                        await self.bot.db.redis.set('pad:monsters', rapidjson.dumps(self.monsters), expire=one_day)

            self.awakenings = await self.bot.db.redis.get('pad:awakenings')
            if not self.awakenings:
                async with self.bot.session.get('https://www.padherder.com/api/awakenings/') as r:
                    if r.status != 200:
                        log.warning('/api/awakenings/ is down')
                    else:
                        self.awakenings = await r.json()
                        await self.bot.db.redis.set('pad:awakenings', rapidjson.dumps(self.awakenings), expire=one_day)
            await asyncio.sleep(3600)

    async def getawaken(self, skills: list) -> None:
        result = []
        if not skills:
            return 'None'
        for x in skills:
            result += self.awakenings[x+1]['name'] + "\n"
        return result

    @staticmethod
    def gettype(type1, type2=None, type3=None):
        types = [
            "Evo Material", "Balanced", "Physical", "Healer", "Dragon", "God",
            "Attacker", "Devil", "Machine", "", "", "", "", "", "Enhance Material"
        ]
        if type2 is None:
            return types[type1]
        elif type3 is None:
            return "{0}/{1}".format(types[type1], types[type2])
        else:
            return "/".join([types[type1], types[type2], types[type3]])

    async def monster_embed(self, mon: dict, author: str) -> discord.Embed:
        title = mon['name']
        description = mon["name_jp"] + "\n" + "*" * mon["rarity"]
        url = 'http://puzzledragonx.com/en/monster.asp?n=' + str(mon['id'])
        em = dmbd.newembed(author, title, description, url)
        em.set_image(url='https://www.padherder.com' + mon['image60_href'])
        em.add_field(name='Type', value=self.gettype(mon['type'], mon['type2'], mon['type3']))
        em.add_field(name='Cost', value=mon['team_cost'])
        em.add_field(name='MaxLv', value="{} ({}xp)".format(mon['max_level'], mon['xp_curve']))
        em.add_field(name='HP', value="[{}][{}]".format(mon['hp_min'], mon['hp_max']))
        em.add_field(name='ATK', value="[{}][{}]".format(mon['atk_min'], mon['atk_max']))
        em.add_field(name='RCV', value="[{}][{}]".format(mon['rcv_min'], mon['rcv_max']))
        em.add_field(name='Leader Skill', value=mon['leader_skill'])
        em.add_field(name='Active Skill', value=mon['active_skill'])
        em.add_field(name='MP Sell Price', value=mon['monster_points'])
        em.add_field(name='Awakenings', value=await self.getawaken(mon['awoken_skills']), inline=False)

        return em

    @commands.command()
    async def pad(self, ctx: commands.Context, *, arg: str) -> None:
        """ Searches a PAD monster"""
        author = ctx.author
        try:
            # If Arg is a number.
            arg = int(arg)
            monster = self.monsters[arg]
            await ctx.send(embed=await self.monster_embed(monster, author))
            return
        except ValueError:
            if len(arg) < 4:
                await ctx.send('Please use more than 3 letters')
                return
            arg = arg.lower()
        except IndexError:
            await ctx.send("ID is not valid.")
            return

        fuzzy = fuzzyset.Fuzzyset()
        fuzzy.add(arg)
        results = []
        # First check if str is too short...
        for (n, m) in enumerate(self.monsters):
            fuzzy_value: tuple = fuzzy.get(m['name'])
            if fuzzy_value is not None:
                results.append((n, fuzzy_value[0][0]))

        sorted_results = sorted(results, key=itemgetter(1), reverse=True)

        if len(sorted_results) > 1:
            possible_results = ["{}: {}".format(n, m[0]['name']) for (n, m) in enumerate(sorted_results)]
            confused = await ctx.send('Which one did you mean? Respond with number.\n' + "\n".join(possible_results))

            def check(msg):
                if msg.content.isdigit():
                    return (msg.author == ctx.author and msg.channel == ctx.channel
                            and 0 <= int(msg.content) < len(results))

            determine = await self.bot.wait_for(
                'message',
                check=check,
                timeout=10
            )

            await confused.delete()
            if determine is None:
                return
            else:
                await ctx.send(embed=await self.monster_embed(results[int(determine.content)], author))
        elif len(results) == 1:
            await ctx.send(embed=await self.monster_embed(sorted_results[0], author))
        else:
            await ctx.send('No Monster Found')


def setup(bot):
    bot.add_cog(PAD(bot))
