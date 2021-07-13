""" Discord Embed Default settings :D """
import random
from time import strftime
from typing import Optional, Union

import discord
from discord import Embed


def newembed(
    a: Union[str, discord.User] = Embed.Empty,
    t: Optional[str] = Embed.Empty,
    d: Optional[str] = Embed.Empty,
    u: Optional[str] = Embed.Empty,
    c: Optional[int] = Embed.Empty,
    footer: Optional[str] = "NinjaKitty",
) -> discord.Embed:
    if c is Embed.Empty:
        c = random.randint(0, 16777215)
    em = discord.Embed(title=t, description=d, url=u, colour=c)
    if a is not Embed.Empty:
        if isinstance(a, discord.User):
            author = a.name + "#" + a.discriminator
            em.set_author(name=author, icon_url=a.avatar_url)
        else:
            em.set_author(name=a)
    em.set_footer(
        text=f"Powered by {footer} | {strftime('%a %b %d, %Y at %I:%M %p')}",
        icon_url="https://cdn.discordapp.com/emojis/432008638756814868.png?v=1",
    )

    return em
