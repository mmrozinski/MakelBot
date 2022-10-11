"""
Responsible for handling miscellaneous commands.

Classes:
    Misc

Functions:
    setup
"""

import random

from discord.ext import commands


class Misc(commands.Cog):
    """
    Contains miscellaneous commands.
    """
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def roll(self, ctx, *args):
        """Sends a message with a random number from 1 to x."""
        if not args:
            await ctx.channel.send(str(random.randint(1, 6)))
        else:
            await ctx.channel.send(str(random.randint(1, int(args[0]))))


async def setup(bot):
    await bot.add_cog(Misc(bot))
