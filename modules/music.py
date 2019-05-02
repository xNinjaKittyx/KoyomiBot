
import asyncio
import logging

from typing import Dict, Optional, Set

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
            'duration': info['duration'],
            'uploader': info['uploader'],
            'title': info['title'],
            'url': info['url'],
            'id': info['id'],
        }

    def __str__(self) -> str:
        fmt = '**{0}** uploaded by {1} and requested by {2}'
        if self.info['duration']:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(self.info['duration'], 60))
        return fmt.format(self.info['title'], self.info['uploader'], self.requester)

    def get_embed(self, title: str) -> discord.Embed:
        desc = str(self)
        if 'https://' in self.info['url']:
            em = dmbd.newembed(title, None, desc, self.info['url'])
            em.set_image(url='https://img.youtube.com/vi/' + self.info['id'] + '/maxresdefault.jpg')
        else:
            em = dmbd.newembed(title, None, desc)

        return em


class VoiceState:
    def __init__(self, bot: discord.Client, voice_channel: discord.VoiceChannel, msg_channel: discord.TextChannel):
        self.current_state = None
        self.voice_channel = voice_channel
        self.msg_channel = msg_channel
        self.voice: discord.VoiceClient = None

        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs: asyncio.Queue[VoiceEntry] = asyncio.Queue()
        self.skip_votes: Set[int] = set()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    async def join(self) -> None:
        self.voice = await self.voice_channel.connect()

    async def move(self, new_voice: discord.VoiceChannel) -> None:
        await self.voice.move_to(new_voice)

    async def leave(self) -> None:
        if self.voice is not None:
            if self.voice.is_playing:
                self.voice.stop()
            try:
                self.audio_player.cancel()
            except asyncio.CancelledError:
                pass
            try:
                await self.voice.disconnect()
            except Exception as e:
                logging.exception(e)
        return

    def skip(self, user: discord.User) -> Optional[str]:
        if self.voice.is_playing():
            self.skip_votes.add(user.id)
            if len(self.skip_votes) > (len(self.voice_channel.members) // 2):
                self.voice.stop()
                return None
            return f"Skip Requested: {len(self.skip_votes)}/{len(self.voice_channel.members) // 2}"
        return None

    def toggle_next(self, error):
        if error:
            logging.exception(error)
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            self.skip_votes.clear()
            await self.msg_channel.send(embed=self.current.get_embed('Now Playing '))
            self.voice.play(self.current.sauce, after=self.toggle_next)
            await self.play_next_song.wait()


class Music(commands.Cog):

    opts = {
        'format': 'bestaudio/best',
        'default-search': 'auto',
        'quiet': True,
        'noplaylist': True,
        'forceurl': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.voice_states: Dict[int, VoiceState] = {}

    def cog_unload(self) -> None:
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except Exception as e:
                logging.error(f"Exception raised: {e}")

    @commands.command(no_pm=True)
    async def join(self, ctx: discord.ext.commands.Context) -> bool:
        """Joins a voice channel."""
        if ctx.author.voice is None:
            await ctx.send(f"{ctx.author} is not in a voice channel.")
            return False
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            state = VoiceState(self.bot, ctx.author.voice.channel, ctx.message.channel)
            try:
                # Bind to a chat and a voice channel.
                await state.join()
            except discord.ClientException:
                await ctx.send(f"Could not join voice channel: {ctx.author.voice.channel.name}")

            self.voice_states[ctx.guild.id] = state
            await ctx.send(f"Music binded to {ctx.author.voice.channel.name} & {ctx.message.channel}")
            return True

        await ctx.send(
            "I am already in a voice channel. You can use `move` or `stop` + `join` to make me join another channel.")
        return True

    async def check_state_and_user(self, state: VoiceState, ctx: commands.Context) -> bool:
        return state.msg_channel != ctx.message.channel or state.voice_channel != ctx.author.voice.channel

    @commands.command(no_pm=True)
    async def move(self, ctx: commands.Context) -> bool:
        if ctx.author.voice is None:
            return False
        state = self.voice_states.get(ctx.guild.id)
        if state is not None:
            if await self.check_state_and_user(state, ctx):
                return False
            await state.move(ctx.author.voice.channel)
            return True

        await ctx.send("I am not in a channel. Use `join` for me to join a voice channel.")
        return True

    @commands.command(no_pm=True)
    async def leave(self, ctx: discord.ext.commands.Context) -> bool:
        if ctx.author.voice is None:
            return False
        state = self.voice_states.get(ctx.guild.id)
        if state is not None:
            if await self.check_state_and_user(state, ctx):
                return False
            await state.leave()
            await ctx.send("Goodbye.")
            del self.voice_states[ctx.guild.id]
        return True

    @commands.command(no_pm=True)
    async def play(self, ctx: commands.Context, *, song: str) -> bool:
        if ctx.author.voice is None:
            return False
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return False
        if await self.check_state_and_user(state, ctx):
            return False

        with youtube_dl.YoutubeDL(self.opts) as ydl:
            song_info = ydl.extract_info(song, download=False)
        bitrate = 0
        url = ''
        codec = ''
        for x in song_info['formats']:
            abr = x.get('abr', 0)
            if 192 >= abr > bitrate:
                url = x['url']
                bitrate = abr
                codec = x['acodec']

        logging.info(url)
        logging.info((codec, bitrate))
        if not url:
            logging.error(f'Could not find a suitable audio for {song}')
            await ctx.send(f'Could not find a suitable audio for {song}')
            return False

        sauce = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url), volume=0.25)
        entry = VoiceEntry(ctx.message, sauce, song_info)
        await ctx.send('Queued: ' + str(entry))
        await state.songs.put(entry)
        return True

    @commands.command(no_pm=True)
    async def volume(self, ctx: commands.Context, value: int) -> bool:
        if ctx.author.voice is None:
            return False
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return False
        if await self.check_state_and_user(state, ctx):
            return False

        if 0 < value <= 100 and state.voice.is_playing():
            state.voice.source.volume = value / 200
            await ctx.send(f'Adjusted volume to {value}')
        return True

    @commands.command(no_pm=True)
    async def pause(self, ctx: commands.Context) -> None:
        """ Pauses the current song."""
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return
        if await self.check_state_and_user(state, ctx):
            return
        if state.voice.is_playing():
            state.voice.pause()
            await ctx.send('Paused Music.')

    @commands.command(no_pm=True)
    async def resume(self, ctx: commands.Context) -> None:
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return
        if await self.check_state_and_user(state, ctx):
            return
        if state.voice.is_paused():
            state.voice.resume()
            await self.refreshplayer(ctx.guild, 'Song has been resumed by ' + str(ctx.author))

    @commands.command(no_pm=True)
    async def now_playing(self, ctx: commands.Context) -> bool:
        state = self.voice_states.get(ctx.guild.id)
        if state is None:
            return False
        if state.current is None:
            await ctx.send('No song is playing')
            return True
        else:
            skip_count = len(state.skip_votes)
            msg = 'Now playing [skips: {}/3]'.format(skip_count)
            await self.refreshplayer(ctx.guild, msg)
            await ctx.message.delete()
            return True

    @commands.command(no_pm=True)
    async def skip(self, ctx: commands.Context) -> bool:
        """Vote to skip a song. The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """
        guild = ctx.guild
        state = self.get_voice_state(guild)
        if not state.voice.is_playing():
            return False

        x = state.skip(ctx.author)
        if x is not None:
            await ctx.send(x)
        return True


def setup(bot: discord.Client) -> None:
    bot.add_cog(Music(bot))
