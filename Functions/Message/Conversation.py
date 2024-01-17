"""
Responsible for handling chatbot conversation related commands

Classes:
    Conversation

Functions:

"""
import discord
from discord.ext import commands
import requests
from Local.Configs.Servers import OLLAMA_SERVER, KOBOLD_SERVER, FASTAPI_SERVER
from transformers import PreTrainedTokenizerFast, LlamaTokenizerFast
import os


class FastAPIConversationLllama2:  # TODO: this is a duplicate from Conversation - solve this sometime
    T_START = "[INST]"
    T_SYSTEM = "<<SYS>>"
    T_SYSTEM_END = "<</SYS>>"
    T_END = "[/INST]"

    def __init__(self):
        self.api_url = FASTAPI_SERVER
        self.session = requests.Session()
        self.tokenizer = LlamaTokenizerFast.from_pretrained("meta-llama/Llama-2-7b-chat-hf", token=True)
        prompt_file = open(os.path.join(os.path.dirname(__file__), "prompt_fastapi.txt"), "r")
        self.system = prompt_file.read()
        self.system_tokens = len(self.tokenizer(self.system).input_ids)
        prompt_file.close()
        self.history = []
        self.max_context_len = 3900

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
            prompt += self.system

        for msg in self.history:
            if msg[1] == "system":
                prompt += (FastAPIConversationLllama2.T_START + " " + FastAPIConversationLllama2.T_SYSTEM + "\n" +
                           msg[0] + "\n" + FastAPIConversationLllama2.T_SYSTEM_END + "\n" +
                           FastAPIConversationLllama2.T_END + "\n")
            elif msg[1] == "user":
                prompt += FastAPIConversationLllama2.T_START + msg[0] + FastAPIConversationLllama2.T_END + "\n"
            elif msg[1] == "model":
                prompt += msg[0] + "\n"

        return prompt

    def reload(self):
        response = requests.get(self.api_url + "/reset")

        if response.status_code != 200:
            raise requests.HTTPError(response)

        self.is_first = True

class KoboldConversationPygmalion2:
    T_SYSTEM = "<|system|>"
    T_USER = "<|user|>"
    T_MODEL = "<|model|>"

    def __init__(self):
        self.api_url = KOBOLD_SERVER + "/api/v1"
        self.options = {
            "use_userscripts": True,
            "stop_sequence": ["###", "\n", KoboldConversationPygmalion2.T_USER, "<|"]
        }
        self.tokenizer = PreTrainedTokenizerFast.from_pretrained("PygmalionAI/pygmalion-2-7b")
        prompt_file = open(os.path.join(os.path.dirname(__file__), "prompt_kobold.txt"), "r")
        self.system = prompt_file.read()
        self.history = []
        self.max_context_len = 2048

        self.reload()

    def generate_from_history(self) -> str:
        data = dict(self.options)

        context_len = sum(list(zip(*self.history))[2])

        if context_len > self.max_context_len:
            self.history.pop(0)
            self.history.pop(0)

        data["prompt"] = self.prompt_from_history()

        response = requests.post(self.api_url + "/generate", json=data)

        if response.status_code != 200:
            self.history.pop()
            raise requests.HTTPError(response)

        result = response.json()["results"][0]["text"].removesuffix("<|")

        self.history.append((result, "model", len(self.tokenizer(result).input_ids)))

        return result

    def generate(self, prompt: str) -> str:
        data = dict(self.options)

        self.history.append((prompt, "user", len(self.tokenizer(prompt).input_ids)))

        context_len = sum(list(zip(*self.history))[2])

        while context_len > self.max_context_len:
            self.history.pop(0)
            self.history.pop(0)
            context_len = sum(list(zip(*self.history))[2])

        data["prompt"] = self.prompt_from_history()

        response = requests.post(self.api_url + "/generate", json=data)

        if response.status_code != 200:
            self.history.pop()
            raise requests.HTTPError(response)

        result = response.json()["results"][0]["text"].removesuffix("<|")

        self.history.append((result, "model", len(self.tokenizer(result).input_ids)))

        return result

    def prompt_from_history(self):
        prompt = ""

        if self.system is not None:
            prompt += KoboldConversationPygmalion2.T_SYSTEM + self.system

        for msg in self.history:
            if msg[1] == "system":
                prompt += KoboldConversationPygmalion2.T_SYSTEM + msg[0]
            elif msg[1] == "user":
                prompt += KoboldConversationPygmalion2.T_USER + msg[0]
            elif msg[1] == "model":
                prompt += KoboldConversationPygmalion2.T_MODEL + msg[0]

        prompt += KoboldConversationPygmalion2.T_MODEL

        return prompt

    def reload(self):
        data = {"name": "Robo default"}
        response = requests.put(self.api_url + "/story/load", json=data)

        if response.status_code != 200:
            raise requests.HTTPError(response)

        # data = {"model": "PygmalionAI/pygmalion-2-7b"}
        #
        # response = requests.get(self.api_url + "/model")
        #
        # if response.status_code != 200:
        #     raise requests.HTTPError(response)
        #
        # current_model = response.json()["result"]
        #
        # if current_model != data["model"]:
        #     response = requests.put(self.api_url + "/model", json=data)
        #
        #     if response.status_code != 200:
        #         raise requests.HTTPError(response)


class GenerationServers:
    Kobold = "kobold"
    Ollama = "ollama"
    FastAPI = "fastapi"


class Conversation(commands.Cog):
    """
    Contains OpenAI conversation related commands

    Methods
    -------
        talk(self, ctx, *args)
    """

    bot: commands.Bot = None

    def __init__(self, bot):
        self.system = None
        self.context = None
        self.bot = bot
        self._last_member = None
        self.conv_channels = set()
        self.options = {}
        self.model = "test1"
        self.server = GenerationServers.FastAPI
        if self.server == GenerationServers.Kobold:
            self.kobold = KoboldConversationPygmalion2()
        elif self.server == GenerationServers.FastAPI:
            self.fastAPI = FastAPIConversationLllama2()

    conv_context_buffer = ""

    @commands.command()
    async def talk(self, ctx: commands.Context, *args):
        async with ctx.channel.typing():
            prompt = ""
            for arg in args:
                prompt += " "
                prompt += arg

            prompt = prompt[1:]

            if self.server == GenerationServers.Ollama:

                data = {
                    "model": self.model,
                    "prompt": prompt,
                    "context": self.context,
                    "stream": False,
                    "options": self.options
                }

                if self.system is not None and self.context is None:
                    data["system"] = self.system

                response = requests.post(OLLAMA_SERVER + "/api/generate", json=data)

                response_json = response.json()
                self.context = response_json["context"]

                await ctx.channel.send(response_json["response"])

            elif self.server == GenerationServers.Kobold:
                result = self.kobold.generate(prompt)
                await ctx.channel.send(result)

            elif self.server == GenerationServers.FastAPI:
                response = self.fastAPI.generate(prompt)
                text = ""
                pause_marks = (".", ",", "!", "?")
                for token in response.iter_lines():
                    token_text = token.decode("utf-8")
                    text += token_text
                    for mark in pause_marks:
                        if mark in token_text:
                            await ctx.channel.send(text)
                            text = ""

    @commands.command()
    async def talk_without_generation(self, ctx: commands.Context, *args):
        prompt = ""
        for arg in args:
            prompt += " "
            prompt += arg

        prompt = prompt[1:]

        if self.server == GenerationServers.Kobold:
            self.kobold.history.append((prompt, "user", len(self.kobold.tokenizer(prompt).input_ids)))

    @commands.command()
    async def talk_generate(self, ctx: commands.Context):
        async with ctx.channel.typing():
            if self.server == GenerationServers.Kobold:
                result = self.kobold.generate_from_history()
                await ctx.channel.send(result)

    @commands.command()
    async def talk_reset(self, ctx):
        if self.server == GenerationServers.Ollama:
            self.context = None
            self.system = None
        elif self.server == GenerationServers.Kobold:
            self.kobold.reload()
        await ctx.channel.send("Successfully reset the conversation context and system prompt!")

    @commands.command()
    async def talk_forget(self, ctx):
        self.context = None
        await ctx.channel.send("Successfully reset the conversation context!")

    @commands.command()
    async def talk_system(self, ctx, *args):
        prompt = ""
        for arg in args:
            prompt += " "
            prompt += arg

        prompt = prompt[1:]

        self.system = prompt

        await ctx.channel.send("Successfully changed the conversation system prompt!")

    @commands.command()
    async def talk_set_parameter(self, ctx, *args):
        if len(args) != 3:
            await ctx.channel.send("Parameter name, value and type (float, int, string) expected!")
            return

        val = None
        if args[2] == "int":
            self.options[args[0]] = int(args[1])
        elif args[2] == "float":
            self.options[args[0]] = float(args[1])
        elif args[2] == "string":
            self.options[args[0]] = args[1]

        await ctx.channel.send("Successfully changed the parameter value!")

    @commands.command()
    async def talk_toggle_listen_channel(self, ctx: commands.Context):
        channel_id = ctx.channel.id
        if channel_id not in self.conv_channels:
            self.conv_channels.add(channel_id)
            await ctx.channel.send("Successfully added this channel to the conversation listening list!\n" +
                                   "All messages sent here will now be passed to the chatbot.\n" +
                                   "Use this command again to disable this feature!")
        else:
            self.conv_channels.remove(channel_id)
            await ctx.channel.send("Successfully removed this channel from the conversation listening list!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id != self.bot.user.id:
            if message.channel.id in self.conv_channels:
                ctx = await self.bot.get_context(message)
                if not ctx.valid:  # Verifies that the message is not a command
                    await ctx.invoke(self.bot.get_command("talk"), message.content)


def setup(bot):
    """
    Called during bot's startup

    :param bot: bot object, passed by Discord's API
    """
    bot.add_cog(Conversation(bot))
