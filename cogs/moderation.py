import datetime
import discord
from discord.ext import commands


# ── Embed builder ─────────────────────────────────────────────────────────────

def _action_embed(
    action: str,
    target: discord.Member | discord.User,
    moderator: discord.Member,
    reason: str,
) -> discord.Embed:
    """Build a red embed for a moderation action (BAN / KICK / UNBAN)."""
    embed = discord.Embed(
        title=f"🔨 {action}",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow(),
    )
    # Target's avatar as the main thumbnail
    embed.set_thumbnail(url=target.display_avatar.url)

    embed.add_field(name="User", value=f"{target.mention}\n`{target}` ({target.id})", inline=True)
    embed.add_field(name="Moderator", value=f"{moderator.mention}\n`{moderator}`", inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text=f"Action: {action}", icon_url=moderator.display_avatar.url)
    return embed


# ── Cog ───────────────────────────────────────────────────────────────────────

class Moderation(commands.Cog):
    """Moderation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Kick ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ):
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot kick someone with an equal or higher role.", ephemeral=True)
            return

        await member.kick(reason=reason)

        embed = _action_embed("KICKED", member, ctx.author, reason)
        await ctx.send(embed=embed)

    # ── Ban ───────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ):
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot ban someone with an equal or higher role.", ephemeral=True)
            return

        await member.ban(reason=reason)

        embed = _action_embed("BANNED", member, ctx.author, reason)
        await ctx.send(embed=embed)

    # ── Unban ─────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="unban", description="Unban a user by their name or ID.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user: str):
        banned_users = [entry async for entry in ctx.guild.bans()]
        for ban_entry in banned_users:
            if str(ban_entry.user) == user or str(ban_entry.user.id) == user:
                await ctx.guild.unban(ban_entry.user)

                embed = _action_embed("UNBANNED", ban_entry.user, ctx.author, "Unbanned manually.")
                await ctx.send(embed=embed)
                return

        await ctx.send(f"No banned user found matching `{user}`.", ephemeral=True)

    # ── Clear ─────────────────────────────────────────────────────────────────

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
