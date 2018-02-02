
import ujson as json

from discord.ext import commands

import utility.discordembed as dmbd

from utility.redis import redis_pool


class PAD:
    def __init__(self, bot):
        self.bot = bot
        # r = requests.get('https://www.padherder.com/api/active_skills/')
        # if r.status_code is not 200:
        #     print('/api/active_skills/ is down')
        # else:
        #     self.active_skills = json.loads(r.text)
        #
        # r = requests.get('https://www.padherder.com/api/evolutions/')
        # if r.status_code is not 200:
        #     print('/api/evolutions/ is down')
        # else:
        #     self.evolutions = json.loads(r.text)
        #
        # r = requests.get('https://www.padherder.com/api/food/')
        # if r.status_code is not 200:
        #     print('/api/food/ is down')
        # else:
        #     self.monsterdb = json.loads(r.text)

    async def refresh(self):
        if await self.bot.redis_pool.get('PADMonsters') is None:
            async with self.bot.session.get('https://www.padherder.com/api/monsters/') as r:
                if r.status != 200:
                    self.bot.logger.warning('/api/monsters/ is down')
                    return False
                await self.bot.redis_pool.set('PADMonsters', await r.read(), ex=43200)
        if await self.bot.redis_pool.get('PADAwakening') is None:
            async with self.bot.session.get('https://www.padherder.com/api/awakenings/') as r:
                if r.status != 200:
                    self.bot.logger.warning('/api/awakenings/ is down')
                    return False
                await self.bot.redis_pool.set('PADAwakening', await r.read(), ex=43200)
        return True

    async def getawaken(self, skills):
        result = ""
        awakenings = json.loads(await self.bot.redis_pool.get('PADAwakening').decode('utf-8'))
        if not skills:
            return 'None'
        for x in skills:
            result += awakenings[x+1]['name'] + "\n"
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

    async def getlink(self, mon, author):
        title = mon['name']
        description = mon["name_jp"] + "\n" + "*" * mon["rarity"]
        url = 'http://puzzledragonx.com/en/monster.asp?n=' + str(mon['id'])
        em = dmbd.newembed(author, title, description, url)
        em.set_image(url='https://www.padherder.com' + mon['image60_href'])
        em.add_field(name='Type', value=self.gettype(mon['type'], mon['type2'], mon['type3']))
        em.add_field(name='Cost', value=mon['team_cost'])
        em.add_field(name='MaxLv', value="{0} ({1}xp)".format(mon['max_level'], mon['xp_curve']))
        em.add_field(name='HP', value="[{0}][{1}]".format(mon['hp_min'], mon['hp_max']))
        em.add_field(name='ATK', value="[{0}][{1}]".format(mon['atk_min'], mon['atk_max']))
        em.add_field(name='RCV', value="[{0}][{1}]".format(mon['rcv_min'], mon['rcv_max']))
        em.add_field(name='Leader Skill', value=str(mon['leader_skill']))
        em.add_field(name='Active Skill', value=str(mon['active_skill']))
        em.add_field(name='MP Sell Price', value=mon['monster_points'])
        em.add_field(name='Awakenings', value=await self.getawaken(mon['awoken_skills']), inline=False)

        await self.bot.cogs['Wordcount'].cmdcount('pad')
        return em

    @commands.command(no_pm=True)
    async def pad(self, ctx, *, arg: str):
        """ Searches a PAD monster"""
        sta = await self.refresh()
        if sta is False:
            return
        monsters = json.loads(redis_pool.get('PADMonsters').decode('utf-8'))
        author = ctx.author
        results = []
        try:
            arg = int(arg)
            if arg in range(1, monsters[-1]['id']+1):
                for (n, x) in enumerate(monsters):
                    if arg == x['id']:
                        await ctx.send(embed=await self.getlink(x, author))
                        return
            await ctx.send("ID is not valid.")
            return
        except ValueError:
            if len(arg) < 4:
                await ctx.send('Please use more than 3 letters')
                return
            arg = arg.lower()
        # First check if str is too short...
        for (n, m) in enumerate(monsters):
            if arg in m['name'].lower():
                results.append(m)

        if len(results) > 1:
            string = ''
            for (n, m) in enumerate(results):
                if arg == m['name'].lower():
                    await ctx.send(embed=await self.getlink(m, author))
                    return
                string += str(n) + ") " + str(m['name']) + '\n'
            confused = await ctx.send('Which one did you mean? Respond with number.\n' + string)

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
                await ctx.send('Didn\'t respond in time...')
            else:
                await ctx.send(embed=await self.getlink(results[int(determine.content)], author))
        elif len(results) == 1:
            await ctx.send(embed=await self.getlink(results[0], author))
        else:
            await ctx.send('No Monster Found')


def setup(bot):
    bot.add_cog(PAD(bot))
