"""
Ticket System
─────────────
• /ticket_panel          — Post the panel (Admin)
• /ticket_setmessage     — Set the welcome message shown inside new tickets (Config Role)
• /ticket_setbutton      — Customise the Open Ticket button (Config Role)
• /ticket_setconfigrole  — Set which role can edit ticket settings (Admin)
• /ticket_setsupport     — Set the support role (Admin)
• /ticket_setlog         — Set the log channel (Admin)
• /ticket_setcategory    — Set the ticket category (Admin)
• /add                   — Add a user to the current ticket (Support)
• /remove                — Remove a user from the current ticket (Support)
• /rename                — Rename the current ticket channel (Support)
"""

import io
import json
import os
import datetime
import discord
from discord.ext import commands
from utils.images import make_action_banner

# ── Config helpers ─────────────────────────────────────────────────────────────

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ticket_config.json")

DEFAULTS: dict = {
    "ticket_counter": 0,
    "welcome_message": (
        "Please describe your issue below and a staff member will be with you shortly.\n\n"
        "To close this ticket, click the **Close Ticket** button."
    ),
    "button_text": "Open Ticket",
    "button_color": "primary",
    "button_emoji": "🎫",
    "config_role_id": None,
    "category_id": None,
    "log_channel_id": None,
    "support_role_id": None,
}


def _load() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in DEFAULTS.items():
            data.setdefault(k, v)
        return data
    return DEFAULTS.copy()


def _save(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def _next_ticket_number() -> str:
    cfg = _load()
    cfg["ticket_counter"] += 1
    _save(cfg)
    return f"{cfg['ticket_counter']:04d}"


def _can_configure(member: discord.Member) -> bool:
    """True if member is admin or has the config role."""
    if member.guild_permissions.administrator:
        return True
    cfg = _load()
    role_id = cfg.get("config_role_id")
    if role_id:
        return any(r.id == int(role_id) for r in member.roles)
    return False


BUTTON_STYLES = {
    "primary": discord.ButtonStyle.primary,
    "blue": discord.ButtonStyle.primary,
    "green": discord.ButtonStyle.success,
    "red": discord.ButtonStyle.danger,
    "grey": discord.ButtonStyle.secondary,
    "gray": discord.ButtonStyle.secondary,
}

EMBED_BLUE = discord.Color.from_rgb(88, 101, 242)
RED = discord.Color.red()
GREEN = discord.Color.green()

# ── Transcript helper ──────────────────────────────────────────────────────────

async def _transcript(channel: discord.TextChannel) -> discord.File:
    lines = [
        f"Transcript — #{channel.name}",
        f"Server : {channel.guild.name}",
        f"Date   : {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "─" * 60,
        "",
    ]
    async for msg in channel.history(limit=500, oldest_first=True):
        ts = msg.created_at.strftime("%Y-%m-%d %H:%M")
        lines.append(f"[{ts}] {msg.author} : {msg.clean_content}")
        for a in msg.attachments:
            lines.append(f"[{ts}] {msg.author} : [Attachment: {a.url}]")
    return discord.File(io.BytesIO("\n".join(lines).encode()), filename=f"{channel.name}-transcript.txt")


# ── Log helper ─────────────────────────────────────────────────────────────────

async def _log(
    guild: discord.Guild,
    action: str,            # "OPENED" | "CLOSED"
    ticket_num: str,
    user: discord.Member | discord.User,
    channel: discord.TextChannel | None = None,
    closer: discord.Member | None = None,
    reason: str | None = None,
    transcript: discord.File | None = None,
):
    cfg = _load()
    log_id = cfg.get("log_channel_id")
    if not log_id:
        return
    log_ch = guild.get_channel(int(log_id))
    if not log_ch:
        return

    color = GREEN if action == "OPENED" else RED
    embed = discord.Embed(
        title=f"🎫 Ticket {action}  —  CHAN-{ticket_num}",
        color=color,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Opened by", value=f"{user.mention}\n`{user}`", inline=True)
    embed.add_field(name="Ticket ID", value=f"CHAN-{ticket_num}", inline=True)
    if channel:
        embed.add_field(name="Channel", value=channel.mention, inline=True)
    if closer:
        embed.add_field(name="Closed by", value=f"{closer.mention}\n`{closer}`", inline=True)
    if reason:
        embed.add_field(name="Close Reason", value=reason, inline=False)

    await log_ch.send(embed=embed, file=transcript)


# ── Views ──────────────────────────────────────────────────────────────────────

class TicketOpenView(discord.ui.View):
    """Panel view — button appearance is read from config each time the panel is posted."""

    def __init__(self):
        super().__init__(timeout=None)
        cfg = _load()

        style = BUTTON_STYLES.get(cfg.get("button_color", "primary"), discord.ButtonStyle.primary)
        raw_emoji = cfg.get("button_emoji") or None
        # Accept plain text emoji or None
        emoji = raw_emoji if raw_emoji and raw_emoji.strip() else None

        btn = discord.ui.Button(
            label=cfg.get("button_text") or "Open Ticket",
            style=style,
            emoji=emoji,
            custom_id="ticket:open",
        )
        btn.callback = self._callback
        self.add_item(btn)

    async def _callback(self, interaction: discord.Interaction):
        cfg = _load()
        guild = interaction.guild
        member = interaction.user

        # Prevent duplicate tickets (stored in topic)
        existing = discord.utils.get(
            guild.text_channels,
            topic=f"TICKET_OWNER:{member.id}",
        )
        if existing:
            await interaction.response.send_message(
                f"You already have an open ticket: {existing.mention}", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        cat_id = cfg.get("category_id")
        sup_id = cfg.get("support_role_id")
        category = guild.get_channel(int(cat_id)) if cat_id else None
        support_role = guild.get_role(int(sup_id)) if sup_id else None

        ticket_num = _next_ticket_number()
        chan_name = f"CHAN-{ticket_num}"

        overwrites: dict = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True, attach_files=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_channels=True,
                read_message_history=True, attach_files=True,
            ),
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                manage_messages=True, attach_files=True,
            )

        channel = await guild.create_text_channel(
            chan_name,
            category=category,
            overwrites=overwrites,
            topic=f"TICKET_OWNER:{member.id}",
        )

        # ── Welcome embed with TICKET banner ──────────────────────────────────
        banner_file = discord.File(make_action_banner("TICKET"), filename="ticket_banner.png")
        welcome_msg = cfg.get("welcome_message") or DEFAULTS["welcome_message"]

        embed = discord.Embed(
            description=f"**Welcome, {member.mention}!**\n\n{welcome_msg}",
            color=EMBED_BLUE,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_image(url="attachment://ticket_banner.png")
        embed.add_field(name="Opened by", value=f"{member.mention} (`{member}`)", inline=True)
        embed.add_field(name="Ticket ID", value=f"CHAN-{ticket_num}", inline=True)
        embed.set_footer(text="Use the buttons below to manage this ticket.")

        mention_str = support_role.mention if support_role else ""
        await channel.send(
            content=f"{member.mention} {mention_str}",
            embed=embed,
            file=banner_file,
            view=TicketControlView(ticket_num=ticket_num, owner_id=member.id),
        )

        # Log creation
        await _log(guild, "OPENED", ticket_num, member, channel=channel)

        await interaction.followup.send(
            f"✅ Your ticket has been created: {channel.mention}", ephemeral=True
        )


class TicketControlView(discord.ui.View):
    """Buttons inside an open ticket."""

    def __init__(self, ticket_num: str = "", owner_id: int = 0):
        super().__init__(timeout=None)
        self.ticket_num = ticket_num
        self.owner_id = owner_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket:close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CloseReasonModal())

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, emoji="✋", custom_id="ticket:claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = _load()
        sup_id = cfg.get("support_role_id")
        support_role = interaction.guild.get_role(int(sup_id)) if sup_id else None
        if support_role and support_role not in interaction.user.roles:
            await interaction.response.send_message(
                "Only support staff can claim tickets.", ephemeral=True
            )
            return
        embed = discord.Embed(
            description=f"✋ **{interaction.user.mention}** has claimed this ticket.",
            color=GREEN,
        )
        await interaction.response.send_message(embed=embed)
        button.disabled = True
        button.label = f"Claimed by {interaction.user.display_name}"
        await interaction.message.edit(view=self)


class CloseReasonModal(discord.ui.Modal, title="Close Ticket"):
    reason = discord.ui.TextInput(
        label="Reason (optional)",
        placeholder="Why is this ticket being closed?",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.channel
        guild = interaction.guild
        closer = interaction.user
        reason_text = self.reason.value or "No reason provided"

        # Extract ticket number from channel name (CHAN-XXXX)
        ticket_num = channel.name.replace("CHAN-", "") if channel.name.startswith("CHAN-") else "????"

        # Find ticket owner from topic
        owner_id = None
        if channel.topic and channel.topic.startswith("TICKET_OWNER:"):
            try:
                owner_id = int(channel.topic.split(":")[1])
            except ValueError:
                pass
        owner = guild.get_member(owner_id) if owner_id else None

        await interaction.response.defer()

        # Build transcript
        trans_file = await _transcript(channel)

        # CLOSED banner
        banner_file = discord.File(make_action_banner("CLOSED"), filename="closed_banner.png")
        close_embed = discord.Embed(
            description=(
                f"🔒 **Ticket closed by {closer.mention}**\n"
                f"**Reason:** {reason_text}\n\n"
                f"This channel will be deleted in **5 seconds**."
            ),
            color=RED,
            timestamp=datetime.datetime.utcnow(),
        )
        close_embed.set_image(url="attachment://closed_banner.png")
        close_embed.set_footer(text=f"Ticket CHAN-{ticket_num}")
        await channel.send(embed=close_embed, file=banner_file)

        # Log closure (send transcript to log channel)
        await _log(
            guild, "CLOSED", ticket_num,
            user=owner or closer,
            closer=closer,
            reason=reason_text,
            transcript=trans_file,
        )

        await discord.utils.sleep_until(
            datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
        )
        await channel.delete(reason=f"Ticket closed by {closer}: {reason_text}")


# ── Cog ────────────────────────────────────────────────────────────────────────

class Tickets(commands.Cog):
    """Ticket system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Re-register persistent views on startup
        bot.add_view(TicketOpenView())
        bot.add_view(TicketControlView())

    # ── Panel ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="ticket_panel", description="Post the ticket panel in this channel. (Admin only)")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx: commands.Context):
        await ctx.defer()

        banner_file = discord.File(make_action_banner("OPEN A TICKET"), filename="panel_banner.png")
        embed = discord.Embed(
            description=(
                "**Need help or have a question?**\n\n"
                "Click the button below to open a private support ticket.\n"
                "A member of our staff team will be with you shortly."
            ),
            color=EMBED_BLUE,
        )
        embed.set_image(url="attachment://panel_banner.png")
        if ctx.guild.icon:
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text=ctx.guild.name)

        await ctx.send(embed=embed, file=banner_file, view=TicketOpenView())

    # ── Config: Welcome Message ────────────────────────────────────────────────

    @commands.hybrid_command(
        name="ticket_setmessage",
        description="Set the welcome message shown when a ticket is opened.",
    )
    async def ticket_setmessage(self, ctx: commands.Context, *, message: str):
        await ctx.defer(ephemeral=True)
        if not _can_configure(ctx.author):
            await ctx.send("You don't have permission to change ticket settings.", ephemeral=True)
            return
        cfg = _load()
        cfg["welcome_message"] = message
        _save(cfg)
        embed = discord.Embed(
            description=f"✅ Welcome message updated:\n\n> {message}",
            color=GREEN,
        )
        await ctx.send(embed=embed, ephemeral=True)

    # ── Config: Button ─────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="ticket_setbutton",
        description="Customise the Open Ticket button (text, color, emoji — all optional).",
    )
    async def ticket_setbutton(
        self,
        ctx: commands.Context,
        text: str | None = None,
        color: str | None = None,
        emoji: str | None = None,
    ):
        await ctx.defer(ephemeral=True)
        if not _can_configure(ctx.author):
            await ctx.send("You don't have permission to change ticket settings.", ephemeral=True)
            return

        valid_colors = list(BUTTON_STYLES.keys())
        if color and color.lower() not in valid_colors:
            await ctx.send(
                f"Invalid color. Choose from: `{'`, `'.join(valid_colors)}`", ephemeral=True
            )
            return

        cfg = _load()
        if text:
            cfg["button_text"] = text
        if color:
            cfg["button_color"] = color.lower()
        if emoji is not None:
            cfg["button_emoji"] = emoji  # empty string clears it

        _save(cfg)

        lines = []
        if text:
            lines.append(f"**Text:** {cfg['button_text']}")
        if color:
            lines.append(f"**Color:** {cfg['button_color']}")
        if emoji is not None:
            lines.append(f"**Emoji:** {cfg['button_emoji'] or '*(none)*'}")

        embed = discord.Embed(
            description="✅ Button updated!\n\n" + "\n".join(lines) + "\n\nRe-run `/ticket_panel` to apply.",
            color=GREEN,
        )
        await ctx.send(embed=embed, ephemeral=True)

    # ── Config: Roles & Channels ───────────────────────────────────────────────

    @commands.hybrid_command(
        name="ticket_setconfigrole",
        description="Set the role that can edit ticket settings.",
    )
    @commands.has_permissions(administrator=True)
    async def ticket_setconfigrole(self, ctx: commands.Context, role: discord.Role):
        await ctx.defer(ephemeral=True)
        cfg = _load()
        cfg["config_role_id"] = role.id
        _save(cfg)
        await ctx.send(f"✅ Config role set to {role.mention}.", ephemeral=True)

    @commands.hybrid_command(
        name="ticket_setsupport",
        description="Set the support role that can see and manage all tickets.",
    )
    @commands.has_permissions(administrator=True)
    async def ticket_setsupport(self, ctx: commands.Context, role: discord.Role):
        await ctx.defer(ephemeral=True)
        cfg = _load()
        cfg["support_role_id"] = role.id
        _save(cfg)
        await ctx.send(f"✅ Support role set to {role.mention}.", ephemeral=True)

    @commands.hybrid_command(
        name="ticket_setlog",
        description="Set the channel where ticket logs are sent.",
    )
    @commands.has_permissions(administrator=True)
    async def ticket_setlog(self, ctx: commands.Context, channel: discord.TextChannel):
        await ctx.defer(ephemeral=True)
        cfg = _load()
        cfg["log_channel_id"] = channel.id
        _save(cfg)
        await ctx.send(f"✅ Log channel set to {channel.mention}.", ephemeral=True)

    @commands.hybrid_command(
        name="ticket_setcategory",
        description="Set the category where ticket channels are created (provide category ID).",
    )
    @commands.has_permissions(administrator=True)
    async def ticket_setcategory(self, ctx: commands.Context, category_id: str):
        await ctx.defer(ephemeral=True)
        try:
            cid = int(category_id)
        except ValueError:
            await ctx.send("Please provide a valid category ID (numbers only).", ephemeral=True)
            return
        cat = ctx.guild.get_channel(cid)
        if not cat or not isinstance(cat, discord.CategoryChannel):
            await ctx.send("Category not found. Make sure you pasted the correct category ID.", ephemeral=True)
            return
        cfg = _load()
        cfg["category_id"] = cid
        _save(cfg)
        await ctx.send(f"✅ Ticket category set to **{cat.name}**.", ephemeral=True)

    # ── In-ticket management ───────────────────────────────────────────────────

    @commands.hybrid_command(name="add", description="Add a member to the current ticket.")
    @commands.has_permissions(manage_channels=True)
    async def add_member(self, ctx: commands.Context, member: discord.Member):
        await ctx.defer()
        if not ctx.channel.name.startswith("CHAN-"):
            await ctx.send("This command can only be used inside a ticket channel.")
            return
        await ctx.channel.set_permissions(
            member, view_channel=True, send_messages=True, read_message_history=True
        )
        embed = discord.Embed(
            description=f"✅ {member.mention} has been added to the ticket.", color=GREEN
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="remove", description="Remove a member from the current ticket.")
    @commands.has_permissions(manage_channels=True)
    async def remove_member(self, ctx: commands.Context, member: discord.Member):
        await ctx.defer()
        if not ctx.channel.name.startswith("CHAN-"):
            await ctx.send("This command can only be used inside a ticket channel.")
            return
        await ctx.channel.set_permissions(member, overwrite=None)
        embed = discord.Embed(
            description=f"❌ {member.mention} has been removed from the ticket.", color=RED
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rename", description="Rename the current ticket channel.")
    @commands.has_permissions(manage_channels=True)
    async def rename_ticket(self, ctx: commands.Context, name: str):
        await ctx.defer()
        if not ctx.channel.name.startswith("CHAN-"):
            await ctx.send("This command can only be used inside a ticket channel.")
            return
        safe = name.lower().replace(" ", "-")
        await ctx.channel.edit(name=f"CHAN-{safe}")
        await ctx.send(f"Ticket renamed to `CHAN-{safe}`.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
