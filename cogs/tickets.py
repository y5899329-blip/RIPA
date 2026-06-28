"""
Multi-Panel Ticket System
─────────────────────────
Each panel has its own ID, welcome message, button style, support role, and category.
All settings are stored in ticket_config.json — no restart required.

Panel management
  /ticket_createpanel <id>              Create a new blank panel
  /ticket_deletepanel <id>              Delete a panel (won't touch open tickets)
  /ticket_listpanels                    List all panels and their key settings
  /ticket_panel       <id>              Post a panel's Open Ticket embed

Per-panel configuration  (Config Role or Admin)
  /ticket_setmessage   <id> <text>      Welcome message shown inside the ticket
  /ticket_setbutton    <id> [text] [color] [emoji]
  /ticket_setsupport   <id> <role>      Support/staff role for this panel
  /ticket_setcategory  <id> <cat_id>    Category where tickets are created

Global configuration  (Admin only)
  /ticket_setconfigrole <role>          Role that can edit ticket settings
  /ticket_setlog        <channel>       Channel for all ticket logs

In-ticket
  /add @user    /remove @user    /rename <name>
"""

import io
import json
import os
import datetime
import discord
from discord.ext import commands
from utils.images import make_action_banner

# ── Config ─────────────────────────────────────────────────────────────────────

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "ticket_config.json"
)

PANEL_DEFAULTS: dict = {
    "welcome_message": (
        "Please describe your issue below and a staff member will be with you shortly.\n\n"
        "To close this ticket, click the **Close Ticket** button."
    ),
    "button_text": "Open Ticket",
    "button_color": "primary",
    "button_emoji": "🎫",
    "support_role_id": None,
    "category_id": None,
}

GLOBAL_DEFAULTS: dict = {
    "ticket_counter": 0,
    "config_role_id": None,
    "log_channel_id": None,
    "panels": {"default": PANEL_DEFAULTS.copy()},
}

BUTTON_STYLES = {
    "primary": discord.ButtonStyle.primary,
    "blue":    discord.ButtonStyle.primary,
    "green":   discord.ButtonStyle.success,
    "red":     discord.ButtonStyle.danger,
    "grey":    discord.ButtonStyle.secondary,
    "gray":    discord.ButtonStyle.secondary,
}

EMBED_BLUE = discord.Color.from_rgb(88, 101, 242)
RED = discord.Color.red()
GREEN = discord.Color.green()
GOLD = discord.Color.gold()


def _load() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in GLOBAL_DEFAULTS.items():
            data.setdefault(k, v)
        if "panels" not in data or not data["panels"]:
            data["panels"] = {"default": PANEL_DEFAULTS.copy()}
        return data
    cfg = GLOBAL_DEFAULTS.copy()
    _save(cfg)
    return cfg


def _save(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def _get_panel(cfg: dict, panel_id: str) -> dict:
    """Return the panel config, filling in any missing keys from PANEL_DEFAULTS."""
    panel = cfg["panels"].get(panel_id, PANEL_DEFAULTS.copy())
    for k, v in PANEL_DEFAULTS.items():
        panel.setdefault(k, v)
    return panel


def _next_ticket_number() -> str:
    cfg = _load()
    cfg["ticket_counter"] += 1
    _save(cfg)
    return f"{cfg['ticket_counter']:04d}"


def _can_configure(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    cfg = _load()
    role_id = cfg.get("config_role_id")
    if role_id:
        return any(r.id == int(role_id) for r in member.roles)
    return False


def _topic(member_id: int, panel_id: str) -> str:
    return f"TICKET_OWNER:{member_id}|PANEL:{panel_id}"


def _parse_topic(topic: str) -> tuple[int | None, str | None]:
    """Return (owner_id, panel_id) from a ticket channel topic, or (None, None)."""
    try:
        parts = dict(p.split(":") for p in topic.split("|"))
        return int(parts["TICKET_OWNER"]), parts["PANEL"]
    except Exception:
        return None, None


# ── Transcript ─────────────────────────────────────────────────────────────────

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
    return discord.File(
        io.BytesIO("\n".join(lines).encode()),
        filename=f"{channel.name}-transcript.txt",
    )


# ── Log helper ─────────────────────────────────────────────────────────────────

async def _log(
    guild: discord.Guild,
    action: str,
    ticket_num: str,
    panel_id: str,
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
        title=f"🎫  Ticket {action}  —  CHAN-{ticket_num}",
        color=color,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Opened by", value=f"{user.mention}\n`{user}`", inline=True)
    embed.add_field(name="Ticket",    value=f"CHAN-{ticket_num}", inline=True)
    embed.add_field(name="Panel",     value=f"`{panel_id}`", inline=True)
    if channel:
        embed.add_field(name="Channel", value=channel.mention, inline=True)
    if closer:
        embed.add_field(name="Closed by", value=f"{closer.mention}\n`{closer}`", inline=True)
    if reason:
        embed.add_field(name="Close Reason", value=reason, inline=False)

    await log_ch.send(embed=embed, file=transcript)


# ── Views ──────────────────────────────────────────────────────────────────────

def _make_open_view(panel_id: str) -> discord.ui.View:
    """
    Build a TicketOpenView for the given panel_id at call time.
    Each panel gets a unique custom_id  →  ticket:open:{panel_id}
    """

    class TicketOpenView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            cfg = _load()
            panel = _get_panel(cfg, panel_id)

            style   = BUTTON_STYLES.get(panel.get("button_color", "primary"), discord.ButtonStyle.primary)
            raw_em  = panel.get("button_emoji") or None
            emoji   = raw_em.strip() if raw_em and raw_em.strip() else None

            btn = discord.ui.Button(
                label=panel.get("button_text") or "Open Ticket",
                style=style,
                emoji=emoji,
                custom_id=f"ticket:open:{panel_id}",
            )
            btn.callback = self._open
            self.add_item(btn)

        async def _open(self, interaction: discord.Interaction):
            cfg = _load()
            if panel_id not in cfg["panels"]:
                await interaction.response.send_message(
                    "This panel no longer exists.", ephemeral=True
                )
                return

            panel  = _get_panel(cfg, panel_id)
            guild  = interaction.guild
            member = interaction.user

            # One ticket per user per panel
            existing = discord.utils.find(
                lambda c: isinstance(c, discord.TextChannel)
                and c.topic == _topic(member.id, panel_id),
                guild.channels,
            )
            if existing:
                await interaction.response.send_message(
                    f"You already have an open **{panel_id}** ticket: {existing.mention}",
                    ephemeral=True,
                )
                return

            await interaction.response.defer(ephemeral=True)

            cat_id = panel.get("category_id")
            sup_id = panel.get("support_role_id")
            category     = guild.get_channel(int(cat_id)) if cat_id else None
            support_role = guild.get_role(int(sup_id))    if sup_id else None

            ticket_num = _next_ticket_number()
            chan_name  = f"CHAN-{ticket_num}"

            overwrites: dict = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True,
                    read_message_history=True, attach_files=True,
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
                topic=_topic(member.id, panel_id),
            )

            # TICKET banner
            banner_file = discord.File(
                make_action_banner("TICKET"), filename="ticket_banner.png"
            )
            welcome_msg = panel.get("welcome_message") or PANEL_DEFAULTS["welcome_message"]

            embed = discord.Embed(
                description=f"**Welcome, {member.mention}!**\n\n{welcome_msg}",
                color=EMBED_BLUE,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_image(url="attachment://ticket_banner.png")
            embed.add_field(name="Opened by", value=f"{member.mention} (`{member}`)", inline=True)
            embed.add_field(name="Ticket ID", value=f"CHAN-{ticket_num}", inline=True)
            embed.add_field(name="Panel",     value=f"`{panel_id}`", inline=True)
            embed.set_footer(text="Use the buttons below to manage this ticket.")

            mention_str = support_role.mention if support_role else ""
            await channel.send(
                content=f"{member.mention} {mention_str}",
                embed=embed,
                file=banner_file,
                view=TicketControlView(),
            )

            await _log(guild, "OPENED", ticket_num, panel_id, member, channel=channel)
            await interaction.followup.send(
                f"✅ Your **{panel_id}** ticket has been created: {channel.mention}",
                ephemeral=True,
            )

    return TicketOpenView()


class TicketControlView(discord.ui.View):
    """Buttons inside every open ticket (close + claim). Panel-agnostic."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket", style=discord.ButtonStyle.danger,
        emoji="🔒", custom_id="ticket:close",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CloseReasonModal())

    @discord.ui.button(
        label="Claim", style=discord.ButtonStyle.success,
        emoji="✋", custom_id="ticket:claim",
    )
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = _load()
        _, panel_id = _parse_topic(interaction.channel.topic or "")
        panel    = _get_panel(cfg, panel_id or "default")
        sup_id   = panel.get("support_role_id")
        sup_role = interaction.guild.get_role(int(sup_id)) if sup_id else None

        if sup_role and sup_role not in interaction.user.roles:
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
        button.label    = f"Claimed by {interaction.user.display_name}"
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
        channel     = interaction.channel
        guild       = interaction.guild
        closer      = interaction.user
        reason_text = self.reason.value or "No reason provided"

        ticket_num = channel.name.replace("CHAN-", "") if channel.name.startswith("CHAN-") else "????"
        owner_id, panel_id = _parse_topic(channel.topic or "")
        panel_id  = panel_id or "default"
        owner     = guild.get_member(owner_id) if owner_id else None

        await interaction.response.defer()

        trans_file  = await _transcript(channel)
        banner_file = discord.File(make_action_banner("CLOSED"), filename="closed_banner.png")

        close_embed = discord.Embed(
            description=(
                f"🔒 **Ticket closed by {closer.mention}**\n"
                f"**Reason:** {reason_text}\n\n"
                "This channel will be deleted in **5 seconds**."
            ),
            color=RED,
            timestamp=datetime.datetime.utcnow(),
        )
        close_embed.set_image(url="attachment://closed_banner.png")
        close_embed.set_footer(text=f"Panel: {panel_id}  •  Ticket: CHAN-{ticket_num}")

        await channel.send(embed=close_embed, file=banner_file)
        await _log(
            guild, "CLOSED", ticket_num, panel_id,
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
    """Multi-panel ticket system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._register_views()

    def _register_views(self):
        """Register persistent views for every existing panel."""
        cfg = _load()
        for panel_id in cfg.get("panels", {}).keys():
            self.bot.add_view(_make_open_view(panel_id))
        self.bot.add_view(TicketControlView())

    # ── Panel lifecycle ────────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="ticket_panel",
        description="Post a ticket panel. Use the panel ID to pick which one.",
    )
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx: commands.Context, panel_id: str = "default"):
        await ctx.defer()
        cfg = _load()
        if panel_id not in cfg["panels"]:
            await ctx.send(
                f"Panel `{panel_id}` doesn't exist. Create it first with `/ticket_createpanel {panel_id}`.",
                ephemeral=True,
            )
            return

        panel_label = panel_id.replace("-", " ").replace("_", " ").title()
        banner_file = discord.File(
            make_action_banner("OPEN A TICKET"), filename="panel_banner.png"
        )
        embed = discord.Embed(
            title=f"{panel_label} Support",
            description=(
                "**Need help or have a question?**\n\n"
                "Click the button below to open a private support ticket.\n"
                "A member of our staff team will be with you shortly."
            ),
            color=EMBED_BLUE,
        )
        embed.set_image(url="attachment://panel_banner.png")
        embed.set_footer(
            text=f"{ctx.guild.name}  •  Panel: {panel_id}",
            icon_url=ctx.guild.icon.url if ctx.guild.icon else None,
        )

        view = _make_open_view(panel_id)
        # Re-register so the new custom_id is known
        self.bot.add_view(view)

        await ctx.send(embed=embed, file=banner_file, view=view)

    @commands.hybrid_command(
        name="ticket_createpanel",
        description="Create a new ticket panel with a given ID.",
    )
    @commands.has_permissions(administrator=True)
    async def ticket_createpanel(self, ctx: commands.Context, panel_id: str):
        await ctx.defer(ephemeral=True)
        panel_id = panel_id.lower().replace(" ", "_")
        cfg = _load()
        if panel_id in cfg["panels"]:
            await ctx.send(f"Panel `{panel_id}` already exists.", ephemeral=True)
            return
        cfg["panels"][panel_id] = PANEL_DEFAULTS.copy()
        _save(cfg)
        # Register persistent view for the new panel
        self.bot.add_view(_make_open_view(panel_id))

        embed = discord.Embed(
            description=(
                f"✅ Panel **`{panel_id}`** created!\n\n"
                f"Configure it with:\n"
                f"• `/ticket_setmessage {panel_id} <text>`\n"
                f"• `/ticket_setbutton {panel_id} [text] [color] [emoji]`\n"
                f"• `/ticket_setsupport {panel_id} @role`\n"
                f"• `/ticket_setcategory {panel_id} <id>`\n\n"
                f"Then post it with `/ticket_panel {panel_id}`."
            ),
            color=GREEN,
        )
        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="ticket_deletepanel",
        description="Delete a ticket panel (existing tickets are not affected).",
    )
    @commands.has_permissions(administrator=True)
    async def ticket_deletepanel(self, ctx: commands.Context, panel_id: str):
        await ctx.defer(ephemeral=True)
        if panel_id == "default":
            await ctx.send("The `default` panel cannot be deleted.", ephemeral=True)
            return
        cfg = _load()
        if panel_id not in cfg["panels"]:
            await ctx.send(f"Panel `{panel_id}` doesn't exist.", ephemeral=True)
            return
        del cfg["panels"][panel_id]
        _save(cfg)
        await ctx.send(f"🗑️ Panel `{panel_id}` deleted.", ephemeral=True)

    @commands.hybrid_command(
        name="ticket_listpanels",
        description="List all ticket panels and their settings.",
    )
    @commands.has_permissions(manage_channels=True)
    async def ticket_listpanels(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        cfg = _load()
        panels = cfg.get("panels", {})

        embed = discord.Embed(
            title="🎫 Ticket Panels",
            description=f"**{len(panels)}** panel(s) configured.",
            color=EMBED_BLUE,
        )
        for pid, panel in panels.items():
            sup_id = panel.get("support_role_id")
            cat_id = panel.get("category_id")
            sup    = ctx.guild.get_role(int(sup_id)).name if sup_id and ctx.guild.get_role(int(sup_id)) else "*(not set)*"
            cat    = ctx.guild.get_channel(int(cat_id)).name if cat_id and ctx.guild.get_channel(int(cat_id)) else "*(not set)*"
            emoji  = panel.get("button_emoji") or "*(none)*"
            embed.add_field(
                name=f"📌  {pid}",
                value=(
                    f"**Button:** {panel.get('button_text', '—')}  {emoji}  `{panel.get('button_color','primary')}`\n"
                    f"**Support role:** {sup}\n"
                    f"**Category:** {cat}\n"
                    f"**Message:** {(panel.get('welcome_message') or '')[:60]}…"
                ),
                inline=False,
            )
        await ctx.send(embed=embed, ephemeral=True)

    # ── Per-panel config ───────────────────────────────────────────────────────

    @commands.hybrid_command(
        name="ticket_setmessage",
        description="Set the welcome message shown inside a panel's tickets.",
    )
    async def ticket_setmessage(self, ctx: commands.Context, panel_id: str, *, message: str):
        await ctx.defer(ephemeral=True)
        if not _can_configure(ctx.author):
            await ctx.send("You don't have permission to change ticket settings.", ephemeral=True)
            return
        cfg = _load()
        if panel_id not in cfg["panels"]:
            await ctx.send(f"Panel `{panel_id}` doesn't exist.", ephemeral=True)
            return
        cfg["panels"][panel_id]["welcome_message"] = message
        _save(cfg)
        await ctx.send(
            embed=discord.Embed(
                description=f"✅ Welcome message for **`{panel_id}`** updated:\n\n> {message}",
                color=GREEN,
            ),
            ephemeral=True,
        )

    @commands.hybrid_command(
        name="ticket_setbutton",
        description="Customise a panel's Open Ticket button (text, color, emoji — all optional).",
    )
    async def ticket_setbutton(
        self,
        ctx: commands.Context,
        panel_id: str,
        text: str | None = None,
        color: str | None = None,
        emoji: str | None = None,
    ):
        await ctx.defer(ephemeral=True)
        if not _can_configure(ctx.author):
            await ctx.send("You don't have permission to change ticket settings.", ephemeral=True)
            return
        if color and color.lower() not in BUTTON_STYLES:
            await ctx.send(
                f"Invalid color. Choose from: `{'`, `'.join(BUTTON_STYLES)}`", ephemeral=True
            )
            return
        cfg = _load()
        if panel_id not in cfg["panels"]:
            await ctx.send(f"Panel `{panel_id}` doesn't exist.", ephemeral=True)
            return
        if text:
            cfg["panels"][panel_id]["button_text"] = text
        if color:
            cfg["panels"][panel_id]["button_color"] = color.lower()
        if emoji is not None:
            cfg["panels"][panel_id]["button_emoji"] = emoji
        _save(cfg)
        p = cfg["panels"][panel_id]
        await ctx.send(
            embed=discord.Embed(
                description=(
                    f"✅ Button for **`{panel_id}`** updated!\n\n"
                    f"**Text:** {p['button_text']}\n"
                    f"**Color:** {p['button_color']}\n"
                    f"**Emoji:** {p.get('button_emoji') or '*(none)*'}\n\n"
                    f"Re-run `/ticket_panel {panel_id}` to apply."
                ),
                color=GREEN,
            ),
            ephemeral=True,
        )

    @commands.hybrid_command(
        name="ticket_setsupport",
        description="Set the support role for a specific ticket panel.",
    )
    @commands.has_permissions(administrator=True)
    async def ticket_setsupport(self, ctx: commands.Context, panel_id: str, role: discord.Role):
        await ctx.defer(ephemeral=True)
        cfg = _load()
        if panel_id not in cfg["panels"]:
            await ctx.send(f"Panel `{panel_id}` doesn't exist.", ephemeral=True)
            return
        cfg["panels"][panel_id]["support_role_id"] = role.id
        _save(cfg)
        await ctx.send(f"✅ Support role for **`{panel_id}`** set to {role.mention}.", ephemeral=True)

    @commands.hybrid_command(
        name="ticket_setcategory",
        description="Set the category where a panel's tickets are created (provide category ID).",
    )
    @commands.has_permissions(administrator=True)
    async def ticket_setcategory(self, ctx: commands.Context, panel_id: str, category_id: str):
        await ctx.defer(ephemeral=True)
        try:
            cid = int(category_id)
        except ValueError:
            await ctx.send("Please provide a valid category ID (numbers only).", ephemeral=True)
            return
        cat = ctx.guild.get_channel(cid)
        if not isinstance(cat, discord.CategoryChannel):
            await ctx.send("Category not found.", ephemeral=True)
            return
        cfg = _load()
        if panel_id not in cfg["panels"]:
            await ctx.send(f"Panel `{panel_id}` doesn't exist.", ephemeral=True)
            return
        cfg["panels"][panel_id]["category_id"] = cid
        _save(cfg)
        await ctx.send(
            f"✅ Category for **`{panel_id}`** set to **{cat.name}**.", ephemeral=True
        )

    # ── Global config ──────────────────────────────────────────────────────────

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
        name="ticket_setlog",
        description="Set the channel where all ticket logs are sent.",
    )
    @commands.has_permissions(administrator=True)
    async def ticket_setlog(self, ctx: commands.Context, channel: discord.TextChannel):
        await ctx.defer(ephemeral=True)
        cfg = _load()
        cfg["log_channel_id"] = channel.id
        _save(cfg)
        await ctx.send(f"✅ Log channel set to {channel.mention}.", ephemeral=True)

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
        await ctx.send(
            embed=discord.Embed(
                description=f"✅ {member.mention} has been added to the ticket.", color=GREEN
            )
        )

    @commands.hybrid_command(name="remove", description="Remove a member from the current ticket.")
    @commands.has_permissions(manage_channels=True)
    async def remove_member(self, ctx: commands.Context, member: discord.Member):
        await ctx.defer()
        if not ctx.channel.name.startswith("CHAN-"):
            await ctx.send("This command can only be used inside a ticket channel.")
            return
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.send(
            embed=discord.Embed(
                description=f"❌ {member.mention} has been removed from the ticket.", color=RED
            )
        )

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
