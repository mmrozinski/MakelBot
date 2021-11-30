import discord
from discord.ext import commands
from discord.ext.commands.core import command

import settings

class message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def clear(self, ctx, arg):
        lst_msg = await ctx.channel.history(limit=int(arg)).flatten()
        await ctx.channel.delete_messages(lst_msg)

        msg = 'Usunięto ostatnie ' + arg + ' wiadomości'
        await ctx.channel.send(msg)

def setup(bot):
    bot.add_cog(message(bot))