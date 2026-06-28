import discord
from discord.ext import commands


class Moderation(commands.Cog):
    """Moderation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot kick someone with an equal or higher role.", ephemeral=True)
            return
        await member.kick(reason=reason)
        await ctx.send(f"Kicked {member.mention}. Reason: {reason}")

    @commands.hybrid_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot ban someone with an equal or higher role.", ephemeral=True)
            return
        await member.ban(reason=reason)
        await ctx.send(f"Banned {member.mention}. Reason: {reason}")

    @commands.hybrid_command(name="unban", description="Unban a user by name or ID.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user: str):
        banned_users = [entry async for entry in ctx.guild.bans()]
        for ban_entry in banned_users:
            if str(ban_entry.user) == user or str(ban_entry.user.id) == user:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"Unbanned {ban_entry.user.mention}.")
                return
        await ctx.send(f"No banned user found matching `{user}`.", ephemeral=True)

    @commands.hybrid_command(name="clear", description="Delete messages in this channel (max 100).")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int = 10):
        amount = min(max(amount, 1), 100)
        await ctx.defer(ephemeral=True)
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"Deleted {len(deleted)} message(s).", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
