"""
Responsible for handling sound related commands

Classes:
    Sound

Functions:
    setup
"""

import Functions.Sound.ytdl as ytdl
from discord.ext import commands

from Functions.Sound import Voice


class Sound(commands.Cog):
    """
    Contains sound related commands
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = Voice.VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    async def cog_before_invoke(self, ctx: commands.Context):
        # Set voice state for every command
        ctx.voice_state = self.get_voice_state(ctx)

    @commands.command(name='join')
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *, search: str):
        """Adds a song to the queue."""
        async with ctx.typing():
            try:
                if search.startswith('https://'):
                    source = await ytdl.YTDLSource.create_source(ctx, search, loop=self.bot.loop)
                else:
                    source = await ytdl.YTDLSource.search_source(self.bot, ctx, search, loop=self.bot.loop)
            except ytdl.YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                if source == 'cancel' or source == 'timeout':
                    await ctx.send('Cancelled')
                else:
                    if not ctx.voice_state.voice:
                        await ctx.invoke(self._join)

                    song = Voice.Song(source)
                    await ctx.voice_state.song_queue.put(song)
                    await ctx.send('Added {} to queue'.format(str(source)))

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Loops or unloops the current queue. (I think)"""

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.send('Looping is now turned ' + ('on' if ctx.voice_state.loop else 'off'))

    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        """Skips the current song."""
        skipped = ctx.voice_state.skip()
        await ctx.send('Skipped ' + skipped.source.title)

    @commands.command(name='stop')
    async def _stop(self, ctx: commands.Context):
        """Stops the player and leaves the channel."""
        await ctx.voice_state.stop()
        await ctx.send('Playback stopped')


async def setup(bot):
    await bot.add_cog(Sound(bot))
