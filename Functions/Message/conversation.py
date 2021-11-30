import discord
from discord.ext import commands
from discord.ext.commands import context
import openai
from openai.api_resources import answer, completion, engine

import settings
import Keys.openaiKey as openaiKey

openai.api_key = openaiKey.KEY

class conversation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        
    qna_context_buffer = ""
    joke_context_buffer = ""
    order_context_buffer = ""

    @commands.command()
    async def qna(self, ctx, *args):
        question = ""
        for arg in args:
            question += " "
            question += arg
        answer = openai.Completion.create(
            engine="curie",
            prompt="I am a highly intelligent question answering bot. If you ask me a question that is rooted in truth, I will give you the answer. If you ask me a question that is nonsense, trickery, or has no clear answer, I will respond with \"Unknown\".\n\n" + self.qna_context_buffer + "Q:" + question + "\nA:",
            temperature=0,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n"]
        )
        self.qna_context_buffer += ("Q: " + question + "\nA: " + answer.choices[0].text + "\n")

        if len(self.qna_context_buffer.split("\n")) > 8:
            self.qna_context_buffer = "\n".join(self.qna_context_buffer.split("\n")[2:])
        await ctx.channel.send(answer.choices[0].text)
    
    @commands.command()
    async def order(self, ctx, *args):
        question = ""
        for arg in args:
            question += " "
            question += arg
        answer = openai.Completion.create(
            engine="curie",
            prompt=self.order_context_buffer + question,
            temperature=0.3,
            max_tokens=60,
            top_p=0.3,
            frequency_penalty=0.5,
            presence_penalty=0,
            stop=["\n"]
            )
        await ctx.channel.send(answer.choices[0].text)
        self.order_context_buffer += ("Q: " + question + "\nA: " + answer.choices[0].text + "\n")

        if len(self.order_context_buffer.split("\n")) > 8:
            self.order_context_buffer = "\n".join(self.order_context_buffer.split("\n")[2:])
        await ctx.channel.send(answer.choices[0].text)

    @commands.command()
    async def joke(self, ctx, *args):
        question = ""
        for arg in args:
            question += " "
            question += arg
        answer = openai.Completion.create(
            engine="curie",
            prompt="Chris is a chatbot that creates funny jokes.\n\nYou: What kind of bees make milk?\nChris: Boobees\n" + self.joke_context_buffer + "You:" + question + "\nChris:",
            temperature=0.8,
            max_tokens=60,
            top_p=1,
            frequency_penalty=0.5,
            presence_penalty=0,
            stop=["\n"]
            )
        self.joke_context_buffer += ("You: " + question + "\nChris: " + answer.choices[0].text + "\n,,")

        if len(self.joke_context_buffer.split("\n")) > 8:
            self.joke_context_buffer = "\n".join(self.joke_context_buffer.split("\n")[2:])
        await ctx.channel.send(answer.choices[0].text)
    

def setup(bot):
    bot.add_cog(conversation(bot))