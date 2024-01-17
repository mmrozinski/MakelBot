"""
Responsible for handling voice receiving related commands and functionalities

Classes:
    Listening

Functions:

"""
import random

import discord
import pyttsx3
from discord.ext import commands, tasks
import speech_recognition as sr
import os
from pydub import AudioSegment
from discord.sinks import RawData
from faster_whisper import WhisperModel
import time
import requests
from Local.Configs.Servers import FASTAPI_SERVER
from transformers import LlamaTokenizerFast
import asyncio

import socket
import requests.packages.urllib3.util.connection as urllib3_cn


def allowed_gai_family():
    """
     https://github.com/shazow/urllib3/blob/master/urllib3/util/connection.py
    """
    family = socket.AF_INET
    if urllib3_cn.HAS_IPV6:
        family = socket.AF_INET  # force ipv4 only if it is available
    return family


urllib3_cn.allowed_gai_family = allowed_gai_family

if os.name == "nt":
    AudioSegment.converter = os.path.dirname(__file__) + "\\..\\..\\ffmpeg\\ffmpeg.exe"

tts_engine = pyttsx3.init()
rate = tts_engine.getProperty('rate')
tts_engine.setProperty("rate", rate + 50)


class FastAPIConversationNoxus:
    T_START = "<|im_start|>"
    T_END = "<|im_end|>"

    def __init__(self):
        self.api_url = FASTAPI_SERVER
        self.session = requests.Session()
        self.tokenizer = LlamaTokenizerFast.from_pretrained("meta-llama/Llama-2-7b-chat-hf", token=True)
        prompt_file = open(os.path.join(os.path.dirname(__file__), "prompt_fastapi_guanaco.txt"), "r")
        self.system = prompt_file.read()
        self.system_tokens = len(self.tokenizer(self.system).input_ids)
        prompt_file.close()
        self.history = []
        self.max_context_len = 3900

        self.name = "Robo"

        self.is_first = True

        self.reload()

    def generate(self, prompt: str) -> requests.Response:
        self.history.append((prompt, "user", len(self.tokenizer(prompt).input_ids)))

        context_len = self.system_tokens + sum(list(zip(*self.history))[2])

        while context_len > self.max_context_len:
            self.history.pop(0)
            self.history.pop(0)
            context_len = self.system_tokens + sum(list(zip(*self.history))[2])

        prompt_to_send = self.prompt_from_history()

        response = self.session.get(self.api_url + "/?prompt=" + prompt_to_send, stream=True)

        if response.status_code != 200:
            raise requests.HTTPError(response)

        return response

    def add_to_history(self, text: str, sender: str):
        self.history.append((text, sender, len(self.tokenizer(text).input_ids)))

    def prompt_from_history(self):
        prompt = ""

        if self.system is not None:
            prompt += FastAPIConversationNoxus.T_START + "system\n" + self.system + FastAPIConversationNoxus.T_END + "\n"

        for msg in self.history[:]:
            if msg[1] == "system":
                prompt += FastAPIConversationNoxus.T_START + "system\n" + msg[0] + FastAPIConversationNoxus.T_END + "\n"
            elif msg[1] == "user":
                prompt += FastAPIConversationNoxus.T_START + "user\n" + msg[0] + FastAPIConversationNoxus.T_END + "\n"
            elif msg[1] == "model":
                prompt += FastAPIConversationNoxus.T_START + "assistant\n" + msg[0] + FastAPIConversationNoxus.T_END + "\n"

        prompt += FastAPIConversationNoxus.T_START + "assistant\n"

        print(prompt)

        return prompt

    def reload(self):
        response = requests.get(self.api_url + "/reset")

        if response.status_code != 200:
            raise requests.HTTPError(response)

        self.is_first = True

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

whisper_model = WhisperModel("medium", device="cuda")

llm_api = FastAPIConversationNoxus()

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
    r.energy_threshold = 300
    file: discord.File

    for file in files:
        with open("tmp_audio_file.wav", "wb") as tmp_file:
            tmp_file.write(file.fp.read())

        if os.name == "nt":
            os.system(".\\ffmpeg\\ffmpeg.exe -y -i .\\tmp_audio_file.wav .\\tmp_audio_file_fixed.wav")
        elif os.name == "posix":
            os.system("ffmpeg -y -i ./tmp_audio_file.wav ./tmp_audio_file_fixed.wav")

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
    files_users = [(discord.File(audio.file, f"{user_id}.{sink.encoding}"), user_id) for user_id, audio in
                   sink.audio_data.items()]

    r = sr.Recognizer()
    r.energy_threshold = 300

    transcriptions = []

    file: discord.File

    if not vc.is_playing():
        for file_user in files_users:
            file = file_user[0]
            user_id = file_user[1]

            if user_id == bot.user.id:
                continue

            username = bot.get_user(user_id).display_name
            with open(os.path.join(os.path.dirname(__file__), "tmp_audio_file.wav"), "wb") as tmp_file:
                tmp_file.write(file.fp.read())

            start_t = time.time()

            segments, _ = whisper_model.transcribe(
                audio=os.path.join(os.path.dirname(__file__), "tmp_audio_file.wav"), vad_filter=True)

            end_t = time.time()

            print("transcription time: ", (end_t - start_t) * 10**3)

            recognized_text = ""

            for segment in segments:
                if segment.text is not None and segment.text != "":
                    recognized_text += segment.text

            if recognized_text != "":
                transcriptions.append((recognized_text, username))

            # with sr.AudioFile("tmp_audio_file_fixed.wav") as source:
            #     audio = r.record(source)
            #     try:
            #         recognized_text = r.recognize_google(audio, language="pl-PL")
            #         transcriptions.append((recognized_text, username))
            #         print(recognized_text)
            #     except sr.UnknownValueError:
            #         pass

        if len(transcriptions) > 0:
            # pick = random.choice(transcriptions)
            prompt = ""
            for pick in transcriptions:
                speaker = pick[1]
                prompt += speaker + ": " + pick[0] + "\n"
            # await ctx.channel.send(prompt)

            start_t = time.time()
            response = llm_api.generate(prompt)

            model_response = ""

            text = ""
            last_play = None
            pause_marks = (".", "!", "?")
            stop_marks = ("[INST]",)

            stop = False
            for token in response.iter_lines():
                token_text = token.decode("utf-8")
                text += token_text
                for mark in pause_marks:
                    if mark in token_text:
                        if last_play is not None:
                            await last_play
                        else:
                            end_t = time.time()
                            print("generation time: ", (end_t - start_t) * 10 ** 3)

                        last_play = asyncio.create_task(do_tts(vc, text))

                        #await ctx.channel.send(text)
                        model_response += text

                        text = ""
                        break

            llm_api.add_to_history(model_response, "model")

            # for line in transcriptions:
            #     speaker = line[1]
            #     prompt = speaker + ": " + line[0]
            #     await ctx.channel.send(prompt)
            #
            #     start_t = time.time()
            #
            #     await ctx.invoke(bot.get_command("talk_without_generation"), prompt)
            #     await ctx.invoke(bot.get_command("talk_generate"))
            #
            #     end_t = time.time()
            #
            #     print("response gen time: ", (end_t - start_t) * 10 ** 3)
            #
            # to_say = (await ctx.channel.history(limit=1).flatten())[0].content
            #
            # start_t = time.time()
            #
            # tts_engine.save_to_file(text=to_say, filename="tmp_speech_file.mp3")
            # tts_engine.runAndWait()
            #
            # end_t = time.time()
            #
            # print("speech gen time: ", (end_t - start_t) * 10 ** 3)
            #
            # dc_audio = discord.FFmpegPCMAudio(source="tmp_speech_file.mp3")
            #
            # vc.play(dc_audio)

    vc.start_recording(
        discord.sinks.WaveSink(),
        stop_listen_recording,
        ctx,
        bot,
        vc
    )

voice_queue = []

async def play_tts(vc: discord.VoiceClient):
    while vc.is_playing():
        await asyncio.sleep(0.1)

    with open("tmp_playing_speech_file.mp3", "wb") as copy_file:
        copy_file.write(voice_queue.pop(0))

    dc_audio = discord.FFmpegOpusAudio(source="tmp_playing_speech_file.mp3")

    vc.play(dc_audio)


async def do_tts(vc: discord.VoiceClient, text: str):
    tts_engine.save_to_file(text=text, filename=f"tmp_speech_file.mp3")
    tts_engine.runAndWait()
    with open("tmp_speech_file.mp3", "rb") as file:
        voice_queue.append(file.read())
    asyncio.create_task(play_tts(vc))


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
            return

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
            return

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
            if vc.recording:
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
            return

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

    @commands.command()
    async def stop_listening(self, ctx: commands.Context):
        if ctx.guild.id in self.connections and ctx.guild.id in self.listen_connections_silence:
            vc: discord.VoiceClient = self.connections[ctx.guild.id]
            if vc.recording:
                vc.stop_recording()

            del self.connections[ctx.guild.id]
            del self.listen_connections_silence[ctx.guild.id]

            await vc.disconnect()
        else:
            await ctx.message.reply("I am currently not listening here.")

    @tasks.loop(seconds=0.25)
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
