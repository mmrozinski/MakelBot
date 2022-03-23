"""
Responsible for handling economy related commands

Classes:
    Economy

Functions:
    setup
"""

from discord.ext import commands


class Economy(commands.Cog):
    """
    Contains economy related commands
    """
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None


def setup(bot):
    bot.add_cog(Economy(bot))
