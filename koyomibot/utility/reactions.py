from typing import Callable, List

import discord


def _get_emojis(msg: discord.Message, emojis: List[str]) -> Callable:
    def check(reaction: discord.Reaction, user: discord.User) -> bool:
        if user.bot:
            return False
        return str(reaction.emoji) in emojis and reaction.message.id == msg.id

    return check


def get_check(msg: discord.Message) -> Callable:
    return _get_emojis(msg, ["✅"])


def get_page_check(msg: discord.Message) -> Callable:
    return _get_emojis(msg, ["◀", "▶", "❌"])
