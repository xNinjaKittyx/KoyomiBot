
import asyncio
import discord
from discord.ext import commands
import youtube_dl

from utility import discordembed as dmbd


class VoiceEntry:
    def __init__(self, message, sauce, info, volume):
        self.requester = message.author
        self.channel = message.channel
        self.sauce = sauce
        self.volume = volume

        # save memory and use only a portion of the info.
        self.info = {
            'duration': info['duration'],
            'uploader': info['uploader'],
            'title': info['title'],
            'url': info['url'],
            'id': info['id'],
        }

    def __str__(self):
        fmt = '**{0}** uploaded by {1} and requested by {2}'
        duration = self.info['duration']
        if duration:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.info['title'], self.info['uploader'], self.requester)

    def get_embed(self, title):
        desc = str(self) + "\nVolume: {}%".format(int(self.volume * 100))
        if 'https://' in self.info['url']:
            em = dmbd.newembed(title, None, desc, self.info['url'])
            em.set_image(url='https://img.youtube.com/vi/' + self.info['id'] + '/maxresdefault.jpg')
        else:
            em = dmbd.newembed(title, None, desc)

        return em


class VoiceState:
    def __init__(self, bot):
        self.current = None  # Current Voice Entry
        self.message = None  # Current Message used.
        self.voice = None    # Current Voice_Client Used
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def skip(self):
        self.skip_votes.clear()
        if self.voice.is_playing():
            self.voice.stop()

    def toggle_next(self, error):
        print(error)
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            self.message = await self.current.channel.send(embed=self.current.get_embed('Now Playing '))
            self.voice.play(self.current.sauce, after=self.toggle_next)
            await self.play_next_song.wait()


class Music:
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, guild):
        state = self.voice_states.get(guild.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[guild.id] = state
        return state

    async def create_voice_client(self, channel):
        voice = await channel.connect()
        state = self.get_voice_state(channel.guild)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                print('something happened')

    async def refreshplayer(self, guild, msg='Currently Playing'):
        state = self.get_voice_state(guild)
        if state.current is None:
            return

        if state.message:
            await state.message.delete()
        state.message = await state.message.channel.send(embed=state.current.get_embed(msg))

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel=None):
        """Joins a voice channel."""
        if ctx.author.voice is None:
            await ctx.send('You are not in a voice channel!')
            return False
        elif channel is None:
            channel = ctx.author.voice.channel
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.get_voice_state(ctx.guild).voice.move_to(channel)
        else:
            await ctx.send('Yay! I\'m in your channel ' + channel.name + ' ready to play anything and everything!')
            return True

    @commands.command()
    async def play(self, ctx, *, song: str):
        state = self.get_voice_state(ctx.guild)
        if not state.voice:
            success = await ctx.invoke(self.join)
            if not success:
                return
        opts = {
            'format': 'bestaudio/best',
            'default-search': 'ytsearch',
            'quiet': True,
            'noplaylist': True,
            'forceurl': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with youtube_dl.YoutubeDL(opts) as ydl:
            song_info = ydl.extract_info(song, download=False)
        bitrate = 0
        url = ''
        for x in song_info['formats']:
            if x['acodec'] == 'opus':
                if x['abr'] > bitrate:
                    bitrate = x['abr']
                    url = x['url']
        sauce = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url), volume=0.5)
        x = await ctx.send('Hold on one moment... Processing your song request.')
        entry = VoiceEntry(ctx.message, sauce, song_info, 0.5)
        await x.delete()
        await ctx.send('Enqueued ' + str(entry))
        await state.songs.put(entry)
        await self.refreshplayer(ctx.guild)


    @commands.command()
    async def volume(self, ctx, value: int):
        state = self.get_voice_state(ctx.guild)
        if 0 < value < 201 and state.voice.is_playing():
            state.voice.source.volume = value / 100
            state.current.volume = value / 100
            await self.refreshplayer(ctx.guild, 'Set volume to {:.0%} by {req}'.format(value / 100, req=ctx.author))

    @commands.command()
    async def pause(self, ctx):
        """ Pauses the current song."""
        state = self.get_voice_state(ctx.guild)
        if state.voice.is_playing():
            state.voice.pause()
            await self.refreshplayer(ctx.guild, 'Song has been paused by ' + str(ctx.author))

    @commands.command()
    async def resume(self, ctx):
        state = self.get_voice_state(ctx.guild)
        if state.voice.is_paused():
            state.voice.resume()
            await self.refreshplayer(ctx.guild, 'Song has been resumed by ' + str(ctx.author))

    @commands.command(aliases=['leave'])
    async def stop(self, ctx):
        state = self.get_voice_state(ctx.guild)
        if state.voice.is_playing:
            _ = await self.refreshplayer(ctx.guild, 'Session ended')
            state.voice.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[ctx.guild.id]
            await state.voice.disconnect()
        except Exception:
            pass

    @commands.command()
    async def playing(self, ctx):

        state = self.get_voice_state(ctx.guild)
        if state.current is None:
            await ctx.send('No song is playing')
        else:
            skip_count = len(state.skip_votes)
            msg = 'Now playing [skips: {}/3]'.format(skip_count)
            await self.refreshplayer(ctx.guild, msg)
            await ctx.message.delete()

    @commands.command(no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """
        guild = ctx.guild
        state = self.get_voice_state(guild)
        if not state.voice.is_playing():
            return

        voter = ctx.author
        if voter == state.current.requester:
            await self.refreshplayer(
                guild,
                'Requester {' + state.current.requester.name +
                '#' + state.current.requester.discriminator +
                ' skipped the following song...'
            )
            state.skip()
        elif voter.id not in state.skip_votes:
            state.skip_votes.add(voter.id)
            total_votes = len(state.skip_votes)
            if total_votes >= 3:
                await self.refreshplayer(guild, 'Skip vote passed, skipping song...')
                state.skip()
            else:
                await self.refreshplayer(guild, 'Skip vote added, currently at [{}/3]'.format(total_votes))
        else:
            await ctx.send('You have already voted to skip this song.')


def setup(bot):
    bot.add_cog(Music(bot))
