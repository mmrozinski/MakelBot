"""
Responsible for handling message management related commands

Classes:
    Message

Functions:
    setup
"""

from discord.ext import commands


class Message(commands.Cog):
    """
    Contains message management related commands
    """
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def clear(self, ctx, arg):
        """Removes last x messages from author's channel."""
        lst_msg = await ctx.channel.history(limit=int(arg)).flatten()
        await ctx.channel.delete_messages(lst_msg)

        msg = 'Usunięto ostatnie ' + arg + ' wiadomości'
        await ctx.channel.send(msg)


async def setup(bot):
    await bot.add_cog(Message(bot))
