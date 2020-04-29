import asyncio
import logging

from typing import Dict, Optional, Set

import async_timeout
import discord
from discord.ext import commands
import youtube_dl

from utility import discordembed as dmbd


class VoiceEntry:
    def __init__(self, message: discord.Message, sauce: str, info: dict):
        self.requester = message.author
        self.sauce = sauce

        # save memory and use only a portion of the info.
        self.info = {
            "duration": info["duration"],
            "uploader": info["uploader"],
            "title": info["title"],
            "url": info["url"],
            "id": info["id"],
        }

    def __str__(self) -> str:
        fmt = "**{0}** uploaded by {1} and requested by {2}"
        if self.info["duration"]:
            fmt = fmt + " [length: {0[0]}m {0[1]}s]".format(divmod(self.info["duration"], 60))
        return fmt.format(self.info["title"], self.info["uploader"], self.requester)

    def get_embed(self, title: str) -> discord.Embed:
        desc = str(self)
        if "https://" in self.info["url"]:
            em = dmbd.newembed(title, None, desc, self.info["url"])
            em.set_image(url="https://img.youtube.com/vi/" + self.info["id"] + "/maxresdefault.jpg")
        else:
            em = dmbd.newembed(title, None, desc)

        return em


class VoiceState:
    def __init__(
        self, bot: discord.Client, voice_channel: discord.VoiceChannel, msg_channel: discord.TextChannel,
    ):
        self.current = None
        self.voice_channel = voice_channel
        self.msg_channel = msg_channel
        self.voice: discord.VoiceClient = None

        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs: asyncio.Queue[VoiceEntry] = asyncio.Queue()
        self.skip_votes: Set[int] = set()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        if self.bot.loop.is_running():
            self.bot.loop.ensure_future(self.leave())
        self.audio_player.cancel()

    async def join(self) -> None:
        self.voice = await self.voice_channel.connect()

    async def move(self, new_voice: discord.VoiceChannel) -> None:
        await self.voice.move_to(new_voice)
        self.voice_channel = new_voice

    async def leave(self) -> None:
        if self.voice is not None and self.voice.is_connected():
            try:
                await self.voice.disconnect()
            except Exception as e:
                logging.exception(e)

    def max_skip(self) -> int:
        return max((len(self.voice_channel.members) - 1) // 2, 1)

    def skip_status(self) -> str:
        return f"{len(self.skip_votes)}/{self.max_skip()}"

    def skip(self, user: discord.User) -> Optional[str]:
        if self.voice.is_playing():
            self.skip_votes.add(user.id)
            if len(self.skip_votes) >= self.max_skip():
                self.voice.stop()
                return None
            return f"Skip Requested: {len(self.skip_votes)}/{self.max_skip()}"
        return None

    def toggle_next(self, error):
        if error:
            logging.exception(error)
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            try:
                self.play_next_song.clear()
                async with async_timeout.timeout(180):
                    self.current = await self.songs.get()
                self.skip_votes.clear()
                await self.msg_channel.send(embed=self.current.get_embed("Now Playing "))
                self.voice.play(self.current.sauce, after=self.toggle_next)
            except asyncio.CancelledError:
                return
            except asyncio.TimeoutError:
                await self.msg_channel.send("No activity within 3 minutes. Exiting.")
                await self.leave()
                return
            except Exception as e:
                logging.exception(error)
            await self.play_next_song.wait()


class Music(commands.Cog):

    opts = {
        "format": "bestaudio/best",
        "default-search": "auto",
        "quiet": True,
        "noplaylist": True,
        "forceurl": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192",}],
    }

    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.voice_states: Dict[int, VoiceState] = {}
        self.bot.loop.create_task(self.clean_voice_states_task())

    async def clean_voice_states_task(self):
        while True:
            clean_guild_ids = []
            logging.info(f"There are currently {len(self.voice_states)} voice states.")
            for guild_id, state in self.voice_states.items():
                if not state or not state.voice or not state.voice.is_connected():
                    clean_guild_ids.append(guild_id)

            for guild_id in clean_guild_ids:
                del self.voice_states[guild_id]

            await asyncio.sleep(30)

    def cog_command_error(self, ctx: discord.ext.commands.Context, error: discord.ext.commands.CommandError) -> None:
        if isinstance(error, discord.ext.commands.CommandInvokeError):
            logging.exception(f"Music Cog Internal Error: {error}")

    def cog_unload(self) -> None:
        for state in self.voice_states.values():
            try:
                self.bot.loop.run_until_complete(state.leave())
            except Exception as e:
                logging.error(f"Exception raised: {e}")

    async def initialize_voice_state(self, ctx: discord.ext.commands.Context) -> Optional[VoiceState]:
        try:
            current_state = self.voice_states[ctx.guild.id]
            if not current_state.voice.is_connected():
                del current_state
            if check_state_and_user(self, current_state, ctx):
                return current_state
            else:
                del current_state
        except KeyError:
            pass

        state = VoiceState(self.bot, ctx.author.voice.channel, ctx.message.channel)
        try:
            # Bind to a chat and a voice channel.
            await state.join()
        except discord.ClientException as e:
            await ctx.send(f"Could not join voice channel: {ctx.author.voice.channel.name}")
            logging.exception(e)
            return None

        self.voice_states[ctx.guild.id] = state
        await ctx.send(f"Music binded to {ctx.author.voice.channel.name} & {ctx.message.channel}")
        return state

    def check_state_and_user(self, state: VoiceState, ctx: commands.Context) -> bool:
        return state.msg_channel != ctx.message.channel or state.voice_channel != ctx.author.voice.channel

    @commands.command(no_pm=True)
    async def join(self, ctx: discord.ext.commands.Context) -> bool:
        """Joins a voice channel."""
        if ctx.author.voice is None:
            await ctx.send(f"{ctx.author} is not in a voice channel.")
            return False
        return bool(await self.initialize_voice_state(ctx))

    @commands.command(no_pm=True)
    async def leave(self, ctx: discord.ext.commands.Context) -> bool:
        if ctx.author.voice is None:
            return False
        state = self.voice_states.get(ctx.guild.id)
        if state is not None:
            if self.check_state_and_user(state, ctx):
                return False
            del state
            await ctx.send("Goodbye.")
        return True

    @commands.command(no_pm=True)
    async def play(self, ctx: commands.Context, *, song: str) -> bool:
        if ctx.author.voice is None:
            return False
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            state = await self.initialize_voice_state(ctx)
        if state is None:
            await ctx.send("Could not join voice channel.")
            return False
        state = self.voice_states.get(ctx.guild.id)
        if self.check_state_and_user(state, ctx):
            return False
        try:
            with youtube_dl.YoutubeDL(self.opts) as ydl:
                song_info = ydl.extract_info(song, download=False)
        except youtube_dl.utils.ExtractorError:
            logging.error(f"Youtube-dl Extractor Error on {song}")
            return False
        except youtube_dl.utils.DownloadError:
            logging.error(f"Youtube-dl Download Error on {song}")
            return False
        bitrate = 0
        url = ""
        codec = ""
        for x in song_info["formats"]:
            abr = x.get("abr", 0)
            if 192 >= abr > bitrate:
                url = x["url"]
                bitrate = abr
                codec = x["acodec"]

        logging.debug(url)
        logging.info((codec, bitrate))
        if not url:
            logging.error(f"Could not find a suitable audio for {song}")
            await ctx.send(f"Could not find a suitable audio for {song}")
            return False

        sauce = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 8",),
            volume=0.25,
        )
        entry = VoiceEntry(ctx.message, sauce, song_info)
        await ctx.send("Queued: " + str(entry))
        await state.songs.put(entry)
        return True

    @commands.command(no_pm=True)
    async def volume(self, ctx: commands.Context, value: int) -> bool:
        if ctx.author.voice is None:
            return False
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return False
        if self.check_state_and_user(state, ctx):
            return False

        if 0 < value <= 100 and state.voice.is_playing():
            state.voice.source.volume = value / 200
            await ctx.send(f"Adjusted volume to {value}")
        return True

    @commands.command(no_pm=True)
    async def pause(self, ctx: commands.Context) -> None:
        """ Pauses the current song."""
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return
        if self.check_state_and_user(state, ctx):
            return
        if state.voice.is_playing():
            state.voice.pause()
            await ctx.send("Paused Music.")

    @commands.command(no_pm=True)
    async def resume(self, ctx: commands.Context) -> None:
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return
        if self.check_state_and_user(state, ctx):
            return
        if state.voice.is_paused():
            state.voice.resume()

    @commands.command(no_pm=True)
    async def current(self, ctx: commands.Context) -> bool:
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return False
        if state.current is None:
            await ctx.send("No song is playing")
            return True
        else:
            msg = f"Now playing [skips: {state.skip_status()}]"
            await ctx.send(embed=state.current.get_embed(msg))
            return True

    @commands.command(no_pm=True)
    async def skip(self, ctx: commands.Context) -> bool:
        """Vote to skip a song. The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return False
        if state.current is None:
            return True
        if not state.voice.is_playing():
            return False

        x = state.skip(ctx.author)
        if x is not None:
            await ctx.send(x)
        return True


def setup(bot: discord.Client) -> None:
    bot.add_cog(Music(bot))
