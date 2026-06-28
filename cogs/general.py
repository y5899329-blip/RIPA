import discord
from discord.ext import commands


class General(commands.Cog):
    """General-purpose commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check the bot's latency.")
    async def ping(self, ctx: commands.Context):
        await ctx.defer()
        await ctx.send(f"Pong! `{round(self.bot.latency * 1000)}ms`")

    @commands.hybrid_command(name="hello", description="Say hello.")
    async def hello(self, ctx: commands.Context):
        await ctx.defer()
        await ctx.send(f"Hello, {ctx.author.mention}!")

    @commands.hybrid_command(name="info", description="Show bot info.")
    async def info(self, ctx: commands.Context):
        await ctx.defer()
        embed = discord.Embed(title="Bot Info", color=discord.Color.blurple())
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users",   value=str(len(self.bot.users)),  inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="help", description="Show all available commands.")
    async def help(self, ctx: commands.Context):
        await ctx.defer()
        embed = discord.Embed(
            title="📋  All Commands",
            description="Use `/` before every command.",
            color=discord.Color.blurple(),
        )

        sections = {
            "🔧 General": [
                ("`/ping`",  "Bot latency."),
                ("`/hello`", "Say hello."),
                ("`/info`",  "Bot stats."),
                ("`/help`",  "This message."),
            ],
            "🔨 Moderation": [
                ("`/ban @user [reason]`",  "Ban — shows a red **BANNED** banner."),
                ("`/kick @user [reason]`", "Kick — shows a red **KICKED** banner."),
                ("`/unban <user>`",        "Unban — shows an **UNBANNED** banner."),
                ("`/clear [amount]`",      "Delete messages (max 100)."),
            ],
            "🎫 Tickets — Panels": [
                ("`/ticket_createpanel <id>`",  "Create a new panel with a custom ID."),
                ("`/ticket_deletepanel <id>`",  "Delete a panel (won't affect open tickets)."),
                ("`/ticket_listpanels`",         "List all panels and their settings."),
                ("`/ticket_panel <id>`",         "Post a panel's embed in this channel."),
            ],
            "⚙️ Tickets — Per-Panel Config": [
                ("`/ticket_setmessage <id> <text>`",              "Welcome message inside the ticket."),
                ("`/ticket_setbutton <id> [text] [color] [emoji]`", "Button text, color and emoji."),
                ("`/ticket_setsupport <id> @role`",               "Support role for this panel."),
                ("`/ticket_setcategory <id> <cat_id>`",           "Category for ticket channels."),
            ],
            "🔒 Tickets — Global Config": [
                ("`/ticket_setconfigrole @role`", "Role that can edit ticket settings."),
                ("`/ticket_setlog #channel`",      "Channel for all ticket logs."),
            ],
            "📂 Tickets — In-Ticket": [
                ("`/add @user`",    "Add a user to the current ticket."),
                ("`/remove @user`", "Remove a user from the current ticket."),
                ("`/rename <name>`","Rename the current ticket channel."),
            ],
        }

        for title, cmds in sections.items():
            embed.add_field(
                name=title,
                value="\n".join(f"{cmd} — {desc}" for cmd, desc in cmds),
                inline=False,
            )

        embed.set_footer(
            text=f"Requested by {ctx.author}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
