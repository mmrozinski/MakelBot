"""
Responsible for handling sound related commands

Classes:
    Sound

Functions:
    setup
"""

import youtube_dl
from discord.ext import commands


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
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, bot):
        self.bot = bot
        self._last_member = None


async def setup(bot):
    """
    Called during bot's startup.

    :param bot: bot object, passed by Discord's API
    """
    await bot.add_cog(Sound(bot))
