import io
import random

from discord import Client, File
from discord.ext import commands
from PIL import Image

# TODO: Needs more jpeg. Jk, this needs to have a separate thread handling the IO.


class ImageManipulator(commands.Cog):
    MAX_SIZE = 8 * 1024 * 1024

    def __init__(self, bot: Client):
        self.bot = bot

    @commands.command()
    async def needsmorejpg(self, ctx: commands.Context, *, link: str) -> None:
        if not link.startswith("http"):
            return
        async with self.bot.session.head(link) as resp:
            if resp.status != 200:
                return
            if "image" in resp.headers["Content-Type"] and int(resp.headers["Content-Length"]) < self.MAX_SIZE:
                pass
            else:
                await ctx.send("Not an image or too big.")
                return

        async with self.bot.session.get(link) as resp:
            if resp.status != 200:
                return

            load_msg = await ctx.send("Adding more jpg...")

            image_data = io.BytesIO(await resp.read())
            image_file = Image.open(image_data).convert(mode="RGB")

        await load_msg.delete()
        f = io.BytesIO()
        image_file.save(f, format="JPEG", quality=random.randint(10, 20))
        await ctx.send("Here's more jpg", file=File(f, filename="more.jpg"))

    @commands.command()
    async def toomuchjpg(self, ctx: commands.Context, *, link: str) -> None:
        if not link.startswith("http"):
            return
        async with self.bot.session.head(link) as resp:
            if resp.status != 200:
                return
            if "image" in resp.headers["Content-Type"] and int(resp.headers["Content-Length"]) < self.MAX_SIZE:
                pass
            else:
                await ctx.send("Not an image or greater than 8 MB.")
                return

        async with self.bot.session.get(link) as resp:
            if resp.status != 200:
                return

            load_msg = await ctx.send("Adding more jpg...")

            image_data = io.BytesIO(await resp.read())
            image_file = Image.open(image_data).convert(mode="RGB")

        await load_msg.delete()
        f = io.BytesIO()
        image_file.save(f, format="JPEG", quality=1)
        await ctx.send("Here's more jpg", file=File(f.getvalue(), filename="toomuchjpg.png"))


def setup(bot: Client) -> None:
    bot.add_cog(ImageManipulator(bot))
