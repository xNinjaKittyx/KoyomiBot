import asyncio
import logging
from typing import Dict, Optional, Set

import async_timeout
import discord
import yt_dlp
from discord.ext import commands

from koyomibot.utility import discordembed as dmbd

log = logging.getLogger(__name__)


class VoiceEntry:
    def __init__(self, message: discord.Message, sauce: discord.PCMVolumeTransformer, info: dict):
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
        log.info(self.info)
        desc = str(self)
        if "https://" in self.info["url"]:
            em = dmbd.newembed(title, self.info["title"], desc, self.info["url"])
            # lowkey takes up too much space in chat.
            # em.set_image(url="https://img.youtube.com/vi/" + self.info["id"] + "/maxresdefault.jpg")
        else:
            em = dmbd.newembed(title, self.info["title"], desc)

        return em


class VoiceState:
    def __init__(
        self,
        bot: discord.Client,
        voice_channel: discord.VoiceChannel,
        msg_channel: discord.TextChannel,
    ):
        self.current: Optional[VoiceEntry] = None
        self.voice_channel = voice_channel
        self.msg_channel = msg_channel
        self.voice: Optional[discord.VoiceClient] = None

        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs: asyncio.Queue[VoiceEntry] = asyncio.Queue()
        self.skip_votes: Set[int] = set()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def __del__(self) -> None:
        if self.bot.loop.is_running():
            asyncio.ensure_future(self.leave())
        self.audio_player.cancel()

    async def update_message(self, embed: discord.Embed):
        """This will update the associated message."""

    async def join(self) -> bool:
        try:
            self.voice = await self.voice_channel.connect(timeout=10)
            return True
        except asyncio.TimeoutError:
            log.warning("Could not join voice chat because of timeout error.")
            return False

    async def move(self, new_voice: discord.VoiceChannel) -> bool:
        if self.voice is None:
            log.warning("Tried to move when not in a voice channel")
            return False
        await self.voice.move_to(new_voice)
        self.voice_channel = new_voice
        return True

    async def leave(self) -> None:
        if self.voice is not None and self.voice.is_connected():
            try:
                await self.voice.disconnect()
            except Exception as e:
                log.exception(e)

    def remove_skip(self, user: discord.User) -> bool:
        try:
            self.skip_votes.remove(user.id)
            return True
        except KeyError:
            return False

    def add_skip(self, user: discord.User) -> bool:
        prev = len(self.skip_votes)
        self.skip_votes.add(user.id)
        return len(self.skip_votes) > prev

    def max_skip(self) -> int:
        return max((len(self.voice_channel.members) - 1) // 2, 1)

    def skip_status(self) -> str:
        return f"{len(self.skip_votes)} / {self.max_skip()}"

    def check_skip(self) -> bool:
        if self.voice is None or self.current is None:
            return False
        if len(self.skip_votes) >= self.max_skip() or self.current.requester.id in self.skip_votes:
            self.voice.stop()
            return True
        return False

    def skip(self, user: discord.User) -> Optional[str]:
        if self.voice is None:
            return None
        if self.voice.is_playing():
            if self.add_skip(user):
                if self.check_skip():
                    return None
                return f"Skip Requested: {self.skip_status()}"
        return None

    def toggle_next(self, error: Exception) -> None:
        if error:
            log.exception(error)
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self) -> None:
        while True:
            try:
                self.play_next_song.clear()
                async with async_timeout.timeout(180):
                    self.current = await self.songs.get()
                self.skip_votes.clear()
                await self.msg_channel.send(embed=self.current.get_embed("Now Playing "))
                if self.voice is not None:
                    if self.voice.source is not None:
                        # FIXME: probably try to get better logic here.
                        self.current.sauce.volume = self.voice.source.volume
                    self.voice.play(self.current.sauce, after=self.toggle_next)
                else:
                    raise Exception("self.voice was None for some reason.")
            except asyncio.CancelledError:
                return
            except asyncio.TimeoutError:
                # I'm not sure how to fix this - The exit message still shows up after leaving.
                if self.voice is None or not self.voice.is_connected():
                    return
                await self.msg_channel.send("No activity within 3 minutes. Exiting.")
                await self.leave()
                return
            except Exception as e:
                log.exception(e)

    async def get_queue(self) -> list:
        # This is generally not a good idea... but it shouldn't be too harmful here.
        return list(self.songs._queue)


class Music(commands.Cog):

    opts = {
        "format": "bestaudio/best",
        "default-search": "auto",
        "quiet": True,
        "noplaylist": True,
        "forceurl": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.voice_states: Dict[int, VoiceState] = {}
        self.bot.loop.create_task(self.clean_voice_states_task())

    async def clean_voice_states_task(self) -> None:
        while True:
            clean_guild_ids = []
            log.debug(f"There are currently {len(self.voice_states)} voice states.")
            for guild_id, state in self.voice_states.items():
                if not state or not state.voice or not state.voice.is_connected():
                    clean_guild_ids.append(guild_id)

            for guild_id in clean_guild_ids:
                del self.voice_states[guild_id]

            await asyncio.sleep(30)

    def cog_command_error(self, ctx: discord.ext.commands.Context, error: discord.ext.commands.CommandError) -> None:
        if isinstance(error, discord.ext.commands.CommandInvokeError):
            log.exception("Music Cog Internal Error: {error}")

    def cog_unload(self) -> None:
        for state in self.voice_states.values():
            try:
                self.bot.loop.run_until_complete(state.leave())
            except Exception as e:
                log.error(f"Exception raised: {e}")

    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        guild_id = member.guild.id
        if guild_id in self.voice_states:
            current_state = self.voice_states[guild_id]
            # We got a voice state related to that voice channel
            if before.channel and before.channel == current_state.voice_channel:
                # User left the channel
                current_state.remove_skip(member)
                current_state.check_skip()

                if len(current_state.voice_channel.members) >= 1:
                    # leave the server, since i'm the only one here
                    await current_state.leave()
                    del self.voice_states[guild_id]

    async def initialize_voice_state(self, ctx: discord.ext.commands.Context) -> Optional[VoiceState]:
        try:
            current_state = self.voice_states[ctx.guild.id]
            # If it's not connected or voice is none, delete this state and make a new one.
            if current_state.voice is None or not current_state.voice.is_connected():
                del self.voice_states[ctx.guild.id]
            elif self.verify_channels(current_state, ctx):
                return current_state
            else:
                del current_state
        except KeyError:
            log.info("VoiceState not found for guild... Continuing...")
            pass

        state = VoiceState(self.bot, ctx.author.voice.channel, ctx.message.channel)
        try:
            # Bind to a chat and a voice channel.
            result = await state.join()
            if not result:
                del state
                return None
        except discord.ClientException as e:
            await ctx.send(f"Could not join voice channel: {ctx.author.voice.channel.name} - {e}")
            log.exception(e)
            return None

        self.voice_states[ctx.guild.id] = state
        await ctx.send(f"Music binded to {ctx.author.voice.channel.name} & {ctx.message.channel}")
        return state

    def verify_channels(self, state: VoiceState, ctx: commands.Context) -> bool:
        """ """
        return (state.msg_channel == ctx.message.channel) and (state.voice_channel == ctx.author.voice.channel)

    @commands.command(no_pm=True, aliases=["summon"])
    async def join(self, ctx: discord.ext.commands.Context) -> bool:
        """Joins a voice channel."""
        if ctx.author.voice is None:
            await ctx.send(f"{ctx.author} is not in a voice channel.")
            return False
        return bool(await self.initialize_voice_state(ctx))

    @commands.command(no_pm=True, aliases=["stop"])
    async def leave(self, ctx: discord.ext.commands.Context) -> bool:
        if ctx.author.voice is None:
            return False
        state = self.voice_states.get(ctx.guild.id)
        if state is not None:
            if not self.verify_channels(state, ctx):
                return False
            await state.leave()
            del state
            await ctx.send("Goodbye.")
        return True

    def get_ytdl_info(self, song: str) -> Optional[dict]:
        try:
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                try:
                    # First try to extract the info on its own.
                    song_info = ydl.extract_info(song, download=False)
                except Exception:
                    # Try to do a search.
                    song_info = ydl.extract_info(f"ytsearch:{song}", download=False)["entries"][0]
                return song_info
        except yt_dlp.utils.ExtractorError:
            log.error(f"Youtube-dl Extractor Error on {song}")
            return None
        except yt_dlp.utils.DownloadError:
            log.error(f"Youtube-dl Download Error on {song}")
            return None

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
        # By this point, it should have it. if not, raise exception
        state = self.voice_states[ctx.guild.id]
        if not self.verify_channels(state, ctx):
            return False
        # If it has too many in queue, give it up.
        if state.songs.qsize() >= 5:
            await ctx.send("Too many songs are in queue.")

        song_info = await self.bot.loop.run_in_executor(None, self.get_ytdl_info, song)

        bitrate = 0
        url = ""
        codec = ""
        for x in song_info["formats"]:
            abr = x.get("abr", 0)
            if 192 >= abr > bitrate:
                url = x["url"]
                bitrate = abr
                codec = x["acodec"]

        log.debug(url)
        log.info((codec, bitrate))
        if not url:
            log.error(f"Could not find a suitable audio for {song}")
            await ctx.send(f"Could not find a suitable audio for {song}")
            return False

        sauce = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 8",
            ),
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
        if state is None or state.voice is None:
            return False
        if not self.verify_channels(state, ctx):
            return False

        prev_volume = state.voice.source.volume

        if 0 < value <= 100 and state.voice.is_playing():
            state.voice.source.volume = value / 200
            await ctx.send(f"Adjusted volume from {prev_volume * 2} to {value}")
        return True

    @commands.command(no_pm=True)
    async def pause(self, ctx: commands.Context) -> None:
        """Pauses the current song."""
        state = self.voice_states.get(ctx.guild.id)
        if state is None or state.voice is None:
            return
        if not self.verify_channels(state, ctx):
            return
        if state.voice.is_playing():
            state.voice.pause()
            await ctx.send("Paused Music.")

    @commands.command(no_pm=True)
    async def resume(self, ctx: commands.Context) -> None:
        state = self.voice_states.get(ctx.guild.id)
        if state is None or state.voice is None:
            return
        if not self.verify_channels(state, ctx):
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
        if state.voice is None:
            return False
        if not state.voice.is_playing():
            return False

        x = state.skip(ctx.author)
        if x is not None:
            await ctx.send(x)
        else:
            await ctx.send("Skipped!")
        return True

    @commands.command(no_pm=True)
    async def queue(self, ctx: commands.Context) -> bool:
        """Prints a list of states."""
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return False
        if state.voice is None:
            return False
        if state.current is None:
            await ctx.send("```Nothing is in the queue.```")
            return True

        final_list = ["```"]
        final_list.extend(
            f"{song.info['title']:<30.30}    {song.info['duration']:<5}    {song.requester.name:<32.32}"
            for song in (await state.get_queue())
        )
        final_list.append("```")

        await ctx.send("\n".join(final_list))

    @commands.command(no_pm=True)
    async def current_voice_channels(self, ctx: commands.Context) -> bool:
        await ctx.send(f"Currently in {len(self.voice_states)} channels")


def setup(bot: discord.Client) -> None:
    bot.add_cog(Music(bot))
