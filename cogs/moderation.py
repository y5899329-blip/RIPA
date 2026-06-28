import discord
from discord.ext import commands


class Moderation(commands.Cog):
    """Moderation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server."""
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot kick someone with an equal or higher role.")
            return
        await member.kick(reason=reason)
        await ctx.send(f"Kicked {member.mention}. Reason: {reason}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member from the server."""
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot ban someone with an equal or higher role.")
            return
        await member.ban(reason=reason)
        await ctx.send(f"Banned {member.mention}. Reason: {reason}")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, user: str):
        """Unban a user by their name or user ID."""
        banned_users = [entry async for entry in ctx.guild.bans()]
        for ban_entry in banned_users:
            if str(ban_entry.user) == user or str(ban_entry.user.id) == user:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"Unbanned {ban_entry.user.mention}.")
                return
        await ctx.send(f"No banned user found matching `{user}`.")

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int = 10):
        """Delete a number of messages (default: 10, max: 100)."""
        amount = min(max(amount, 1), 100)
        deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"Deleted {len(deleted) - 1} message(s).")
        await msg.delete(delay=3)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
