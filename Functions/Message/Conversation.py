"""
Responsible for handling chatbot conversation related commands

Classes:
    Conversation

Functions:

"""
import discord
from discord.ext import commands
import requests
from Local.Configs.Servers import OLLAMA_SERVER


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

    conv_context_buffer = ""

    @commands.command()
    async def talk(self, ctx:  commands.Context, *args):
        async with ctx.channel.typing():
            prompt = ""
            for arg in args:
                prompt += " "
                prompt += arg

            prompt = prompt[1:]

            data = {
                "model": "llama2-uncensored",
                "prompt": prompt,
                "context": self.context,
                "stream": False  # TODO: handle the stream of responses (editing the message maybe?)
            }

            if self.system is not None:
                data["system"] = self.system

            response = requests.post("http://" + OLLAMA_SERVER + "/api/generate", json=data)

            response_json = response.json()
            self.context = response_json["context"]

            # self.qna_context_buffer += ("Q: " + question + "\nA: " + answer.choices[0].text + "\n")
            #
            # if len(self.qna_context_buffer.split("\n")) > 8:
            #     self.qna_context_buffer = "\n".join(self.qna_context_buffer.split("\n")[2:])
        await ctx.channel.send(response_json["response"])

    @commands.command()
    async def talk_reset(self, ctx):
        self.context = None
        self.system = None
        await ctx.channel.send("Successfully reset the conversation context!")

    @commands.command()
    async def talk_system(self, ctx, *args):
        self.context = None

        prompt = ""
        for arg in args:
            prompt += " "
            prompt += arg

        prompt = prompt[1:]

        self.system = prompt

        await ctx.channel.send("Successfully changed the conversation system prompt!")

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
