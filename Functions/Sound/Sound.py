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

    Attributes
    ----------
    YTDL_OPTIONS : dict
        YTDL configuration options
    FFMPEG_OPTIONS : dict
        FFMPEG configuration options
    ytdl : youtube_dl.FileDownloader
        YTDL FileDownloader object

    Methods
    -------

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
        """
        Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        """

        async with ctx.typing():
            try:
                source = await ytdl.YTDLSource.search_source(self.bot, ctx, search, loop=self.bot.loop)
            except ytdl.YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                if not ctx.voice_state.voice:
                    await ctx.invoke(self._join)

                song = Voice.Song(source)
                await ctx.voice_state.song_queue.put(song)
                await ctx.send('Added {} to queue'.format(str(source)))


def setup(bot):
    """
    Called during bot's startup.

    :param bot: bot object, passed by Discord's API
    """
    bot.add_cog(Sound(bot))
