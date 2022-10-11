"""
Responsible for handling information providing commands

Classes:
    Info

Functions:
    setup
"""

import discord
from discord.ext import commands

import settings


class Info(commands.Cog):
    """
    Contains information providing commands
    """

    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def info(self, ctx):
        """Provides basic information about the bot"""
        info_board = discord.Embed(
            title=settings.BotName,
            description="Podstawy kodu tego bota mogły, ale nie musiały, zostać bezczelnie ukradzione z GitHuba",
            colour=discord.Colour.dark_purple()
        )
        info_board.set_footer(text=settings.BotOwner)
        info_board.add_field(name="Komendy", value="Wpisz " + settings.Prefix + "help aby pokazać listę komend.",
                             inline=True)
        await ctx.send(embed=info_board)

    @commands.command()
    async def avatar(self, ctx):
        """Sends a message with author's avatar"""
        await ctx.send(ctx.author.avatar_url)

    @commands.command()
    async def help(self, ctx, *input):
        """Sends a message with information on available commands"""
        info_board = discord.Embed(
            title=settings.BotName,
            colour=discord.Colour.dark_purple()
        )
        info_board.set_footer(text=settings.BotOwner)

        if not input:
            for cog in self.bot.cogs:
                info_board.add_field(name=cog.lower(), value=f'{self.bot.cogs[cog].__doc__}\n')
        else:
            for cog in self.bot.cogs:
                if cog.lower() == input[0].lower():
                    for command in self.bot.get_cog(cog).get_commands():
                        info_board.add_field(name=f'{settings.Prefix}{command.name}',
                                             value=f'{command.help}\n')
                    break
            else:
                await ctx.send(f'{input[0]} is not a valid category!')
                return

        await ctx.send(embed=info_board)


async def setup(bot):
    await bot.add_cog(Info(bot))
