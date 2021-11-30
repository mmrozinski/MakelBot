import discord
from discord.ext import commands
import json

import settings
import Local.Users.user as User

class users(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
    
    @commands.command()
    async def addUser(self, ctx):
        user = User.User(ctx.message.author.discriminator, 10)
        user.save()

def setup(bot):
    bot.add_cog(users(bot))