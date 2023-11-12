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

    Methods
    -------
        roll(ctx, *args)
    """
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def roll(self, ctx, *args):
        """
        Sends a message with a random number from 1 to x.

        :param ctx: context object
        :param args: command arguments (x)
        """
        if not args:
            await ctx.channel.send(str(random.randint(1, 6)))
        else:
            await ctx.channel.send(str(random.randint(1, int(args[0]))))

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx):
        await ctx.bot.tree.sync()
        await ctx.send("Synced!")


def setup(bot):
    """
        Called during bot's startup

        :param bot: bot object, passed by Discord's API
    """
    bot.add_cog(Misc(bot))
