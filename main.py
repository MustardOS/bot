import json
import sys

import discord
from discord import app_commands

import command
import event

if len(sys.argv) < 2:
    print("Usage: python main.py <BOT TOKEN>")
    sys.exit(1)

TOKEN = sys.argv[1]

with open("config.json", "r") as f:
    CONFIG = json.load(f)

with open("commands.json", "r") as f:
    COMMAND_DEFS = json.load(f)

GUILD_ID = discord.Object(id=CONFIG["guild_id"])

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True


class BlobBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await command.load_commands(self, COMMAND_DEFS, GUILD_ID, CONFIG)
        self.tree.copy_global_to(guild=GUILD_ID)
        await self.tree.sync(guild=GUILD_ID)


client = BlobBot()
event.register(client, CONFIG)
client.run(TOKEN)
