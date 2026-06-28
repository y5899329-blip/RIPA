import datetime
import discord
from discord.ext import commands
from utils.images import make_action_banner


async def _send_action(
    ctx: commands.Context,
    action: str,
    target: discord.Member | discord.User,
    moderator: discord.Member,
    reason: str,
):
    filename = f"{action.lower()}.png"
    banner_file = discord.File(make_action_banner(action), filename=filename)

    embed = discord.Embed(color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
    embed.set_image(url=f"attachment://{filename}")
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(
        name="User",
        value=f"{target.mention}\n`{target}` ({target.id})",
        inline=True,
    )
    embed.add_field(
        name="Moderator",
        value=f"{moderator.mention}\n`{moderator}`",
        inline=True,
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(
        text=f"Action executed by {moderator}",
        icon_url=moderator.display_avatar.url,
    )
    await ctx.send(embed=embed, file=banner_file)


class Moderation(commands.Cog):
    """Moderation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        reason: str = "No reason provided",
    ):
        await ctx.defer()
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot kick someone with an equal or higher role.")
            return
        await member.kick(reason=reason)
        await _send_action(ctx, "KICKED", member, ctx.author, reason)

    @commands.hybrid_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        reason: str = "No reason provided",
    ):
        await ctx.defer()
        if member.top_role >= ctx.author.top_role:
            await ctx.send("You cannot ban someone with an equal or higher role.")
            return
        await member.ban(reason=reason)
        await _send_action(ctx, "BANNED", member, ctx.author, reason)

    @commands.hybrid_command(name="unban", description="Unban a user by their name or ID.")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user: str):
        await ctx.defer()
        banned_users = [entry async for entry in ctx.guild.bans()]
        for ban_entry in banned_users:
            if str(ban_entry.user) == user or str(ban_entry.user.id) == user:
                await ctx.guild.unban(ban_entry.user)
                await _send_action(ctx, "UNBANNED", ban_entry.user, ctx.author, "Manually unbanned.")
                return
        await ctx.send(f"No banned user found matching `{user}`.")

    @commands.hybrid_command(name="clear", description="Delete messages in this channel (max 100).")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int = 10):
        await ctx.defer(ephemeral=True)
        amount = min(max(amount, 1), 100)
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"Deleted {len(deleted)} message(s).", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
