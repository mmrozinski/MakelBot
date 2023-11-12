"""
Responsible for handling voice receiving related commands and functionalities

Classes:
    Listening

Functions:

"""
import random
from io import BytesIO

import discord
from discord.ext import commands, tasks
import speech_recognition as sr
import os
from gtts import gTTS

from discord.sinks import RawData


# This most likely is a crime against clean code, but it works
# Anyway, later on I might want to consider changing another method further down to check which users were active last frame
# Also, consider using a timestamp to check the duration of silence
def my_unpack_audio(self, data):
    if 200 <= data[1] <= 204:
        return
    if self.paused:
        return

    data = RawData(data, self)

    if data.decrypted_data == b"\xf8\xff\xfe":
        self.wasLastFrameSilence = True
        return

    self.wasLastFrameSilence = False
    self.decoder.decode(data)


discord.VoiceClient.wasLastFrameSilence = True
discord.VoiceClient.unpack_audio = my_unpack_audio


async def once_done(sink: discord.sinks.Sink, channel: discord.TextChannel,
                    *args):  # Our voice client already passes these in.
    recorded_users = [  # A list of recorded users
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    await sink.vc.disconnect()  # Disconnect from the voice channel.
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in
             sink.audio_data.items()]  # List down the files.
    await channel.send(f"finished recording audio for: {', '.join(recorded_users)}.",
                       files=files)  # Send a message with the accumulated files.


async def once_done_with_stt(sink: discord.sinks.Sink, channel: discord.TextChannel,
                             *args):
    recorded_users = [
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    await sink.vc.disconnect()
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in
             sink.audio_data.items()]
    await channel.send(f"finished recording audio for: {', '.join(recorded_users)}.")

    r = sr.Recognizer()
    file: discord.File

    for file in files:
        with open("tmp_audio_file.wav", "wb") as tmp_file:
            tmp_file.write(file.fp.read())

        os.remove("tmp_audio_file2.wav")
        os.system(".\\ffmpeg\\ffmpeg.exe -i .\\tmp_audio_file.wav .\\tmp_audio_file_fixed.wav")

        with sr.AudioFile("tmp_audio_file_fixed.wav") as source:
            audio = r.record(source)
            try:
                recognized_text = r.recognize_google(audio, language="en-IT")
                await channel.send(f"Audio transcription: \"{recognized_text}\"")
            except sr.UnknownValueError:
                await channel.send(f"*Unintelligible*")
            except sr.RequestError as e:
                print("Transcription error; {0}".format(e))


async def stop_listen_recording(sink: discord.sinks.Sink, ctx: commands.Context, bot: discord.Bot,
                                vc: discord.VoiceClient,
                                *args):
    recorded_users = [
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in
             sink.audio_data.items()]

    r = sr.Recognizer()

    transcriptions = []

    file: discord.File

    for file in files:
        with open("tmp_audio_file.wav", "wb") as tmp_file:
            tmp_file.write(file.fp.read())

        os.system(".\\ffmpeg\\ffmpeg.exe -y -i .\\tmp_audio_file.wav .\\tmp_audio_file_fixed.wav")

        with sr.AudioFile("tmp_audio_file_fixed.wav") as source:
            audio = r.record(source)
            try:
                recognized_text = r.recognize_google(audio, language="en-IT")
                transcriptions.append(recognized_text)
                print(recognized_text)
            except sr.UnknownValueError:
                pass

    if len(transcriptions) > 0:
        await ctx.invoke(bot.get_command("talk"), random.choice(transcriptions))

        to_say = (await ctx.channel.history(limit=1).flatten())[0].content
        voice = gTTS(text=to_say, lang="en", slow=False)

        voice.save("tmp_speech_file.mp3")

        dc_audio = discord.FFmpegPCMAudio(source="tmp_speech_file.mp3",
                                          executable="C:\\Users\\Makel\\PycharmProjects\\MakelBot\\ffmpeg\\ffmpeg.exe")

        vc.play(dc_audio)

    vc.start_recording(
        discord.sinks.WaveSink(),
        stop_listen_recording,
        ctx,
        bot,
        vc
    )


class Listening(commands.Cog):
    bot: commands.Bot = None
    connections = {}
    listen_connections_silence = {}

    def __init__(self, bot):
        self.system = None
        self.context = None
        self.bot = bot
        self._last_member = None

        self.listen.start()

    @commands.command()
    async def record(self, ctx: commands.Context):  # If you're using commands.Bot, this will also work.
        voice = ctx.author.voice

        if not voice:
            await ctx.message.reply("You aren't in a voice channel!")

        vc: discord.VoiceClient = await voice.channel.connect()  # Connect to the voice channel the author is in.
        self.connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

        vc.start_recording(
            discord.sinks.WaveSink(),  # The sink type to use.
            once_done,  # What to do once done.
            ctx.channel  # The channel to disconnect from.
        )
        await ctx.message.reply("Started recording!")

    @commands.command()
    async def transcribe(self, ctx: commands.Context):  # If you're using commands.Bot, this will also work.
        voice = ctx.author.voice

        if not voice:
            await ctx.message.reply("You aren't in a voice channel!")

        vc: discord.VoiceClient = await voice.channel.connect()  # Connect to the voice channel the author is in.
        self.connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

        vc.start_recording(
            discord.sinks.WaveSink(),  # The sink type to use.
            once_done_with_stt,  # What to do once done.
            ctx.channel  # The channel to disconnect from.
        )
        await ctx.message.reply("Started recording!")

    @commands.command()
    async def stop_recording(self, ctx: commands.Context):
        if ctx.guild.id in self.connections:  # Check if the guild is in the cache.
            vc = self.connections[ctx.guild.id]
            vc.stop_recording()  # Stop recording, and call the callback (once_done).
            del self.connections[ctx.guild.id]  # Remove the guild from the cache.
            await ctx.message.delete()  # And delete.
        else:
            await ctx.message.reply("I am currently not recording here.")  # Respond with this if we aren't recording.

    @commands.command()
    async def start_listening(self, ctx: commands.Context):
        voice = ctx.author.voice

        if not voice:
            await ctx.message.reply("You aren't in a voice channel!")

        vc: discord.VoiceClient = await voice.channel.connect(timeout=float("inf"))
        self.connections.update({ctx.guild.id: vc})
        self.listen_connections_silence.update({ctx.guild.id: [vc, False]})

        vc.start_recording(
            discord.sinks.WaveSink(),
            stop_listen_recording,
            ctx,
            self.bot,
            vc
        )
        await ctx.message.reply("Started listening!")

    @tasks.loop(seconds=1)
    async def listen(self):
        for guild in self.listen_connections_silence.keys():
            vc = self.listen_connections_silence[guild][0]
            if self.listen_connections_silence[guild][1]:
                self.listen_connections_silence[guild][1] = vc.wasLastFrameSilence
                if self.listen_connections_silence[guild][1] and vc.recording:
                    vc.stop_recording()
            else:
                self.listen_connections_silence[guild][1] = vc.wasLastFrameSilence


def setup(bot):
    """
    Called during bot's startup

    :param bot: bot object, passed by Discord's API
    """
    bot.add_cog(Listening(bot))
