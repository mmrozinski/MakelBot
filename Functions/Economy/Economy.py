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

    Methods
    -------
    """
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None


def setup(bot):
    """
    Called during bot's startup

    :param bot: bot object, passed by Discord's API
    """
    bot.add_cog(Economy(bot))
