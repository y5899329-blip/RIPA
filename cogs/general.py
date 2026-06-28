import discord
from discord.ext import commands


class General(commands.Cog):
    """General-purpose commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Check the bot's latency."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! `{latency}ms`")

    @commands.command(name="hello")
    async def hello(self, ctx: commands.Context):
        """Say hello."""
        await ctx.send(f"Hello, {ctx.author.mention}!")

    @commands.command(name="info")
    async def info(self, ctx: commands.Context):
        """Show bot info."""
        embed = discord.Embed(
            title="Bot Info",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(len(self.bot.users)), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
