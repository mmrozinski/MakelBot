import discord
from discord.ext import commands

import settings

class economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

def setup(bot):
    bot.add_cog(economy(bot))