import discord
from discord import app_commands, SelectOption
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

LOGS_CHANNEL_NAME = "ticket-logs"
TICKET_CATEGORY_NAME = "Tickets"
user_tickets = {}

class ConfirmCloseModal(Modal):
    def __init__(self, ticket_channel):
        super().__init__(title="Confirm Close")
        self.ticket_channel = ticket_channel
        self.confirmation = TextInput(label="Type 'CLOSE' to confirm", style=discord.TextStyle.short)
        self.add_item(self.confirmation)

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirmation.value.upper() == "CLOSE":
            await interaction.response.send_message(embed=discord.Embed(description="Closing the ticket...", color=discord.Color.red()), ephemeral=True)
            user_tickets.pop(interaction.user.id, None)
            await self.ticket_channel.delete()
            logs_channel = discord.utils.get(self.ticket_channel.guild.channels, name=LOGS_CHANNEL_NAME)
            if logs_channel:
                embed = discord.Embed(title="Ticket Closed", description=f"Ticket {self.ticket_channel.name} closed by {interaction.user.mention}.", color=discord.Color.red())
                await logs_channel.send(embed=embed)
        else:
            await interaction.response.send_message(embed=discord.Embed(description="Ticket close canceled.", color=discord.Color.orange()), ephemeral=True)

class TicketButton(Button):
    def __init__(self, label, style, ticket_channel=None, claim_button=False):
        super().__init__(label=label, style=style)
        self.ticket_channel = ticket_channel
        self.claim_button = claim_button
        self.claimed = False
        self.claimed_by = None

    async def callback(self, interaction: discord.Interaction):
        if self.claim_button:
            if self.claimed:
                await interaction.response.send_message(embed=discord.Embed(description=f"This ticket has already been claimed by {self.claimed_by.mention}.", color=discord.Color.red()), ephemeral=True)
            else:
                self.claimed = True
                self.claimed_by = interaction.user
                await interaction.response.send_message(embed=discord.Embed(description=f"{interaction.user.mention} has claimed this ticket.", color=discord.Color.blue()), ephemeral=False)
                await interaction.message.edit(view=self.view)
        elif self.label == "Close Ticket":
            modal = ConfirmCloseModal(self.ticket_channel)
            await interaction.response.send_modal(modal)

class TicketActionView(View):
    def __init__(self, ticket_channel):
        super().__init__(timeout=None)
        self.ticket_channel = ticket_channel
        self.add_item(TicketButton(label="Claim Ticket", style=discord.ButtonStyle.primary, ticket_channel=ticket_channel, claim_button=True))
        self.add_item(TicketButton(label="Close Ticket", style=discord.ButtonStyle.danger, ticket_channel=ticket_channel))

class TicketDropdown(Select):
    def __init__(self):
        options = [
            SelectOption(label="Open Ticket", description="Click to open a new ticket.", emoji="📩")
        ]
        super().__init__(placeholder="Choose an option...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id in user_tickets:
            await interaction.response.send_message(embed=discord.Embed(description="You already have an open ticket. Please close your existing ticket before opening a new one.", color=discord.Color.red()), ephemeral=True)
            return

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        ticket_channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category)
        user_tickets[interaction.user.id] = ticket_channel.id

        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(guild.default_role, read_messages=False, send_messages=False)

        embed = discord.Embed(title="New Ticket", description=f"{interaction.user.mention} has opened a ticket.", color=discord.Color.green())
        await ticket_channel.send(embed=embed, view=TicketActionView(ticket_channel))

        logs_channel = discord.utils.get(guild.channels, name=LOGS_CHANNEL_NAME)
        if not logs_channel:
            logs_channel = await guild.create_text_channel(LOGS_CHANNEL_NAME)

        log_embed = discord.Embed(title="Ticket Opened", description=f"Ticket {ticket_channel.name} opened by {interaction.user.mention}.", color=discord.Color.green())
        await logs_channel.send(embed=log_embed)

        await interaction.response.send_message(embed=discord.Embed(description=f"Ticket created: {ticket_channel.mention}", color=discord.Color.blue()), ephemeral=True)

class TicketDropdownView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="ticket", description="Open a ticket.")
async def ticket_command(interaction: discord.Interaction):
    view = TicketDropdownView()
    embed = discord.Embed(title="Ticket System", description="Use the dropdown below to open a ticket.", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=view)

bot.run("MTI3OTM1MTk3Mzg3MDY5ODU1OQ.GrL0Tr.fTDLgd95MsM4yiFePh5tNxJN0bDflYpTn_IWa8")