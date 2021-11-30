import discord
from discord.ext import commands

import settings

class info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def info(self, ctx):
        info_board = discord.Embed(
            title=settings.BotName,
            description="Podstawy kodu tego bota mogły, ale nie musiały, zostać bezczelnie ukradzione z GitHuba",
            colour=discord.Colour.dark_purple()
        )
        info_board.set_footer(text=settings.BotOwner)
        info_board.add_field(name="Komendy", value="Wpisz " + settings.Prefix + "help aby pokazać listę komend.", inline=True)
        await ctx.send(embed=info_board)

    @commands.command()
    async def avatar(self, ctx):
        await ctx.send(ctx.author.avatar_url)

    @commands.command()
    async def help(self, ctx):
        info_board = discord.Embed(
            title=settings.BotName,
            colour=discord.Colour.dark_purple()
        )
        info_board.set_footer(text=settings.BotOwner)
        info_board.add_field(name=settings.Prefix + "avatar", value="Wyświetla twój awatar", inline=False)
        info_board.add_field(name=settings.Prefix + "info", value="Informacje o bocie", inline=False)
        info_board.add_field(name=settings.Prefix + "roll (X)", value="Rzut DX (domyślnie D6)", inline=False)
        await ctx.send(embed=info_board)

def setup(bot):
    bot.add_cog(info(bot))