import discord
from discord.ext import commands


class General(commands.Cog):
    """General-purpose commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check the bot's latency.")
    async def ping(self, ctx: commands.Context):
        await ctx.defer()
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! `{latency}ms`")

    @commands.hybrid_command(name="hello", description="Say hello.")
    async def hello(self, ctx: commands.Context):
        await ctx.defer()
        await ctx.send(f"Hello, {ctx.author.mention}!")

    @commands.hybrid_command(name="info", description="Show bot info.")
    async def info(self, ctx: commands.Context):
        await ctx.defer()
        embed = discord.Embed(title="Bot Info", color=discord.Color.blurple())
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(len(self.bot.users)), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="help", description="Show all available commands.")
    async def help(self, ctx: commands.Context):
        await ctx.defer()
        embed = discord.Embed(
            title="📋 All Commands",
            description="Here's everything I can do. Use `/` before each command.",
            color=discord.Color.blurple(),
        )
        sections = {
            "🔧 General": [
                ("`/ping`", "Check the bot's latency."),
                ("`/hello`", "Say hello."),
                ("`/info`", "Show bot info."),
                ("`/help`", "Show this message."),
            ],
            "🔨 Moderation": [
                ("`/ban @user [reason]`", "Ban a member — shows a red BANNED banner image."),
                ("`/kick @user [reason]`", "Kick a member — shows a red KICKED banner image."),
                ("`/unban <user#tag or ID>`", "Unban a previously banned user."),
                ("`/clear [amount]`", "Delete messages in the channel (max 100)."),
            ],
            "🎫 Tickets": [
                ("`/ticket_panel`", "Post the Open Ticket panel. *(Admin only)*"),
                ("`/add @user`", "Add a member to the current ticket."),
                ("`/remove @user`", "Remove a member from the current ticket."),
                ("`/rename <name>`", "Rename the current ticket channel."),
            ],
        }
        for section, cmds in sections.items():
            value = "\n".join(f"{cmd} — {desc}" for cmd, desc in cmds)
            embed.add_field(name=section, value=value, inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
