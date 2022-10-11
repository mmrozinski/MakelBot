"""
Responsible for handling user management related commands

Classes:
    Users

Functions:
    setup
"""

from discord.ext import commands

import Local.Users.User as User


class Users(commands.Cog):
    """Contains user management related commands"""
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def addUser(self, ctx):
        """Adds a new user to the user database"""
        user = User.User(ctx.Message.author.discriminator, 10)
        user.save()


async def setup(bot):
    await bot.add_cog(Users(bot))
