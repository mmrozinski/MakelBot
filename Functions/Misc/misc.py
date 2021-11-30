import discord
from discord.ext import commands
import random

import settings

class misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def roll(self, ctx, *args):
        if not args:
            await ctx.channel.send(str(random.randint(1, 6)))
        else:
            await ctx.channel.send(str(random.randint(1, int(args[0]))))

def setup(bot):
    bot.add_cog(misc(bot))