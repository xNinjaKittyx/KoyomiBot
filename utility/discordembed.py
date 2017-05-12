""" Discord Embed Default settings :D """
from time import strftime
import random

import discord

def newembed(a=None, t=None, d=None, u=None, c=None):
    if c is None:
        c = random.randint(0, 16777215)
    em = discord.Embed(title=t, description=d, url=u, colour=c)
    if a is not None:
        author = a.name + '#' + a.discriminator
        em.set_author(name=author, icon_url=a.avatar_url)
    em.set_footer(
        text="Powered by NinjaKitty | " +
        strftime('%a %b %d, %Y at %I:%M %p'),
        icon_url="https://my.mixtape.moe/yaoznj.png"
    )

    return em
