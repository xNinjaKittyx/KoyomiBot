""" Discord Embed Default settings :D """
import random

from time import strftime
from typing import Optional, Union

import discord


def newembed(
    a: Union[str, discord.User] = None, t: Optional[str] = None,
    d: Optional[str] = None, u: Optional[str] = None, c: Optional[int] = None,
    footer: Optional[str] = "NinjaKitty"
) -> discord.Embed:
    if c is None:
        c = random.randint(0, 16777215)
    em = discord.Embed(title=t, description=d, url=u, colour=c)
    if a is not None:
        if isinstance(a, discord.User):
            author = a.name + '#' + a.discriminator
            em.set_author(name=author, icon_url=a.avatar_url)
        else:
            em.set_author(name=a)
    em.set_footer(
        text=f"Powered by {footer} | {strftime('%a %b %d, %Y at %I:%M %p')}",
        icon_url="https://my.mixtape.moe/yaoznj.png"
    )

    return em
