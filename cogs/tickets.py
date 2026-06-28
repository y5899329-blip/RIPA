import os
import io
import datetime
import discord
from discord.ext import commands

CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", 0) or 0)
LOG_CHANNEL_ID = int(os.getenv("TICKET_LOG_CHANNEL_ID", 0) or 0)
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID", 0) or 0)

EMBED_COLOR = discord.Color.from_rgb(88, 101, 242)
CLOSE_COLOR = discord.Color.red()
SUCCESS_COLOR = discord.Color.green()


def _ticket_number(guild: discord.Guild) -> str:
    count = sum(1 for ch in guild.text_channels if ch.name.startswith("ticket-"))
    return str(count + 1).zfill(4)


async def _build_transcript(channel: discord.TextChannel) -> discord.File:
    lines: list[str] = [
        f"Transcript for #{channel.name}",
        f"Server : {channel.guild.name}",
        f"Date   : {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "─" * 60,
        "",
    ]
    async for msg in channel.history(limit=500, oldest_first=True):
        ts = msg.created_at.strftime("%Y-%m-%d %H:%M")
        lines.append(f"[{ts}] {msg.author} : {msg.clean_content}")
        for att in msg.attachments:
            lines.append(f"[{ts}] {msg.author} : [Attachment: {att.url}]")
    content = "\n".join(lines).encode()
    return discord.File(io.BytesIO(content), filename=f"{channel.name}-transcript.txt")


class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="ticket:open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower().replace(' ', '-')}")
        if existing:
            await interaction.response.send_message(f"You already have an open ticket: {existing.mention}", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        category = guild.get_channel(CATEGORY_ID) if CATEGORY_ID else None
        support_role = guild.get_role(SUPPORT_ROLE_ID) if SUPPORT_ROLE_ID else None
        ticket_num = _ticket_number(guild)

        overwrites: dict = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True),
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)

        channel = await guild.create_text_channel(
            f"ticket-{ticket_num}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket opened by {member} ({member.id})",
        )

        embed = discord.Embed(
            title=f"Ticket #{ticket_num}",
            description=(
                f"Welcome {member.mention}!\n\n"
                "Please describe your issue and a staff member will be with you shortly.\n\n"
                "Click **Close Ticket** when your issue has been resolved."
            ),
            color=EMBED_COLOR,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=f"Opened by {member}", icon_url=member.display_avatar.url)

        mention_str = support_role.mention if support_role else ""
        await channel.send(content=f"{member.mention} {mention_str}", embed=embed, view=TicketControlView())
        await interaction.followup.send(f"Your ticket has been created: {channel.mention}", ephemeral=True)


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket:close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CloseReasonModal())

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, emoji="✋", custom_id="ticket:claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        support_role = interaction.guild.get_role(SUPPORT_ROLE_ID) if SUPPORT_ROLE_ID else None
        if support_role and support_role not in interaction.user.roles:
            await interaction.response.send_message("Only support staff can claim tickets.", ephemeral=True)
            return
        embed = discord.Embed(description=f"✋ {interaction.user.mention} has claimed this ticket.", color=SUCCESS_COLOR)
        await interaction.response.send_message(embed=embed)
        button.disabled = True
        button.label = f"Claimed by {interaction.user.display_name}"
        await interaction.message.edit(view=self)


class CloseReasonModal(discord.ui.Modal, title="Close Ticket"):
    reason = discord.ui.TextInput(
        label="Reason (optional)",
        placeholder="Why is this ticket being closed?",
        required=False,
        max_length=300,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.channel
        guild = interaction.guild
        closer = interaction.user
        reason_text = self.reason.value or "No reason provided"

        await interaction.response.defer()
        transcript_file = await _build_transcript(channel)

        log_channel = guild.get_channel(LOG_CHANNEL_ID) if LOG_CHANNEL_ID else None
        if log_channel:
            log_embed = discord.Embed(title=f"Ticket Closed — #{channel.name}", color=CLOSE_COLOR, timestamp=datetime.datetime.utcnow())
            log_embed.add_field(name="Closed by", value=closer.mention, inline=True)
            log_embed.add_field(name="Reason", value=reason_text, inline=True)
            log_embed.add_field(name="Channel", value=channel.name, inline=True)
            await log_channel.send(embed=log_embed, file=transcript_file)

        close_embed = discord.Embed(
            description=f"🔒 Closed by {closer.mention}. Reason: {reason_text}\n\nDeleting in 5 seconds...",
            color=CLOSE_COLOR,
        )
        await channel.send(embed=close_embed)
        await discord.utils.sleep_until(datetime.datetime.utcnow() + datetime.timedelta(seconds=5))
        await channel.delete(reason=f"Ticket closed by {closer}: {reason_text}")


class Tickets(commands.Cog):
    """Ticket system commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.add_view(TicketOpenView())
        bot.add_view(TicketControlView())

    @commands.hybrid_command(name="ticket_panel", description="Post the ticket panel in this channel. (Admin only)")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx: commands.Context):
        await ctx.defer()
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="Need help? Click the button below to open a private support ticket.\n\nA member of staff will assist you as soon as possible.",
            color=EMBED_COLOR,
        )
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        await ctx.send(embed=embed, view=TicketOpenView())

    @commands.hybrid_command(name="add", description="Add a member to the current ticket.")
    @commands.has_permissions(manage_channels=True)
    async def add_member(self, ctx: commands.Context, member: discord.Member):
        await ctx.defer()
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.send("This command can only be used inside a ticket channel.")
            return
        await ctx.channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
        embed = discord.Embed(description=f"✅ {member.mention} has been added to the ticket.", color=SUCCESS_COLOR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="remove", description="Remove a member from the current ticket.")
    @commands.has_permissions(manage_channels=True)
    async def remove_member(self, ctx: commands.Context, member: discord.Member):
        await ctx.defer()
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.send("This command can only be used inside a ticket channel.")
            return
        await ctx.channel.set_permissions(member, overwrite=None)
        embed = discord.Embed(description=f"❌ {member.mention} has been removed from the ticket.", color=CLOSE_COLOR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rename", description="Rename the current ticket channel.")
    @commands.has_permissions(manage_channels=True)
    async def rename_ticket(self, ctx: commands.Context, name: str):
        await ctx.defer()
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.send("This command can only be used inside a ticket channel.")
            return
        safe_name = name.lower().replace(" ", "-")
        await ctx.channel.edit(name=f"ticket-{safe_name}")
        await ctx.send(f"Ticket renamed to `ticket-{safe_name}`.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
