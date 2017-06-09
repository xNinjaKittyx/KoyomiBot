
import asyncio
import discord
from discord.ext import commands
from utility import discordembed as dmbd


class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = '**{0.title}** uploaded by {0.uploader} and requested by {1.display_name}'
        duration = self.player.duration
        if duration:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

    def getembed(self, title):
        desc = str(self) + "\nVolume: {}%".format(int(self.player.volume * 100))
        if 'https://' in self.player.url:
            info_dict = self.player.yt.extract_info(self.player.url, download=False)
            video_id = info_dict.get("id", None)
            em = dmbd.newembed(self.requester, title, desc, self.player.url)
            em.set_image(url='https://img.youtube.com/vi/' + video_id + '/maxresdefault.jpg')
        else:
            em = dmbd.newembed(self.requester, title, desc)

        return em

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.current_msg = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set()  # a set of user_ids that voted
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)


    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            self.current_msg = await self.current.channel.send(embed=self.current.getembed('Now Playing '))
            self.current.player.start()
            await self.play_next_song.wait()


class Music:
    """Voice related commands.
    Works in multiple guilds at once.
    """
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
                pass

    async def refreshplayer(self, guild, msg='Currently Playing'):
        state = self.get_voice_state(guild)
        if state.current is None:
            return
        temp = await state.current_msg.channel.send(embed=state.current.getembed(msg))
        await state.current_msg.delete()
        state.current_msg = temp

    @commands.command(no_pm=True)
    async def join(self, ctx, *, channel: discord.Channel):
        """Joins a voice channel."""
        try:
            await self.create_voice_client(channel)
        except discord.InvalidArgument:
            x = await ctx.send('```This is not a voice channel...```')
        except discord.ClientException:
            x = await ctx.send('```Already in a voice channel...```')
        else:
            x = await ctx.send('```Ready to play audio in ' + channel.name + '```')
        self.bot.cogs['Wordcount'].cmdcount('join')

    @commands.command(no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""
        if ctx.author.voice is None:
            x = await ctx.send('```You are not in a voice channel.```')
            return False
        else:
            summoned_channel = ctx.author.voice.channel

        state = self.get_voice_state(ctx.guild)
        if state.voice is None:
            state.voice = await summoned_channel.connect()
        else:
            await state.voice.move_to(summoned_channel)

        self.bot.cogs['Wordcount'].cmdcount('summon')
        return True

    @commands.command(no_pm=True)
    async def play(self, ctx, *, song : str):
        """Plays a song.
        If there is a song currently in the queue, then it is
        queued until the next song is done playing.
        This command automatically searches as well from YouTube.
        The list of supported sites can be found here:
        https://rg3.github.io/youtube-dl/supportedsites.html
        """
        state = self.get_voice_state(ctx.guild)
        opts = {
            'default-search': 'ytsearch',
            'quiet': True,
            'noplaylist': True,
            'forceurl': True
        }

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await ctx.channel.send(fmt.format(type(e).__name__, e))
        else:
            player.volume = 0.25
            entry = VoiceEntry(ctx.message, player)
            await ctx.send('Enqueued ' + str(entry) + '')
            await state.songs.put(entry)
            await self.refreshplayer(ctx.guild)
            await ctx.message.delete()


        self.bot.cogs['Wordcount'].cmdcount('play')

    @commands.command(no_pm=True)
    async def volume(self, ctx, value: int):
        """Sets the volume of the currently playing song."""

        state = self.get_voice_state(ctx.guild)
        if state.is_playing():
            if value > 200 or value < 1:
                await self.refreshplayer(ctx.guild, 'Value too high! 1 - 200 only!')
            else:
                player = state.player
                player.volume = value / 100
                await self.refreshplayer(ctx.guild, 'Set the volume to {:.0%}'.format(player.volume))
        await ctx.message.delete()
        self.bot.cogs['Wordcount'].cmdcount('volume')

    @commands.command(no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.guild)
        if state.is_playing():
            player = state.player
            player.pause()
            await self.refreshplayer(ctx.guild, 'Paused')
        await ctx.message.delete()

        self.bot.cogs['Wordcount'].cmdcount('pause')

    @commands.command(no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.guild)
        if state.is_playing():
            player = state.player
            player.resume()
            await self.refreshplayer(ctx.guild, 'Resumed')
        await ctx.message.delete()
        self.bot.cogs['Wordcount'].cmdcount('resume')

    @commands.command(no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue. Permissions System will come soon.
        """
        guild = ctx.guild
        state = self.get_voice_state(guild)

        if state.is_playing():
            _ = await self.refreshplayer(guild, 'Session ended')
            player = state.player
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[guild.id]
            await state.voice.disconnect()
        except:
            pass

    @commands.command(no_pm=True)
    async def skip(self, ctx):
        """Vote to skip a song. The song requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """
        guild = ctx.guild
        state = self.get_voice_state(guild)
        if not state.is_playing():
            await ctx.send('```Not playing any music right now...```')
            return

        voter = ctx.author
        if voter == state.current.requester:
            await self.refreshplayer(
                guild,
                'Requester {' + state.current.requester.name +
                '#' + state.current.requester.discriminator +
                ' requested skipping song...'
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
            await ctx.send('```You have already voted to skip this song.```')

        await ctx.message.delete()

        self.bot.cogs['Wordcount'].cmdcount('skip')

    @commands.command(no_pm=True)
    async def playing(self, ctx):
        """Shows info about the currently played song."""

        state = self.get_voice_state(ctx.guild)
        if state.current is None:
            await ctx.send('No songs are playing!')
        else:
            skip_count = len(state.skip_votes)
            msg = 'Now playing [skips: {}/3]'.format(skip_count)
            await self.refreshplayer(ctx.guild, msg)
            await ctx.message.delete()

        self.bot.cogs['Wordcount'].cmdcount('playing')

def setup(bot):
    bot.add_cog(Music(bot))
