import asyncio
import itertools
import random

from copy import deepcopy

import discord
import Functions.Sound.ytdl as ytdl
from async_timeout import timeout
from discord.ext import commands


class VoiceError(Exception):
    pass

class Song:
    """Represents a single YTDL song"""
    __slots__ = ('source', 'requester')

    def __init__(self, source: ytdl.YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        """Makes a **sick** embed for the song"""
        embed = (discord.Embed(title='Now playing', description='```css\n{0.source.title}\n```'.format(self),
                               color=discord.Color.purple())
                        .add_field(name='Duration', value=self.source.duration)
                        .add_field(name='Requested by', value=self.requester.mention)
                        .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                        .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                        .set_thumbnail(url=self.source.thumbnail)
                        .set_author(name=self.requester.name, icon_url=self.requester.avatar_url))
        return embed


class SongQueue(asyncio.Queue):
    """Song queue, based on asyncio's Queue"""
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    """Represents the voice state of the bot"""
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self.ctx = ctx

        self.voice = None

        self.song_queue = SongQueue()
        self.current = None
        self.next = asyncio.Event()

        self.current_message = None

        self.exists = True
        self.loop = False

        self.volume = 1.
        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            self.now = None

            if self.loop and self.current:
                await self.song_queue.put(Song(self.current.source))

            if self.current_message:
                await self.current_message.delete()

            try:
                async with timeout(180):  # 3 minutes
                    self.current = await self.song_queue.get()
            except asyncio.TimeoutError:
                self.bot.loop.create_task(self.stop())
                self.exists = False
                return

            self.current.source.volume = self.volume
            self.voice.play(self.current.source, after=self.play_next_song)
            self.current_message = await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        skipped = self.current
        if self.is_playing:
            self.voice.stop()

        return skipped

    async def stop(self):
        self.song_queue.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None
            await self.current_message.delete()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    @loop.setter
    def loop(self, value):
        self._loop = value
