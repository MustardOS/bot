import random

import discord


async def load_commands(client, command_defs, guild_id):
    client.tree.clear_commands(guild=guild_id)

    for cmd in command_defs:
        name = cmd.get("name")
        description = cmd.get("description", "No description provided")
        ctype = cmd.get("type")

        if ctype == "static":
            register_static_command(client, name, description, cmd.get("response", ""), guild_id)

        elif ctype == "random":
            register_random_command(client, name, description, cmd.get("responses", []), guild_id)

        elif ctype == "action" and name == "reload":
            responses = cmd.get("response", {})
            register_reload_command(client, name, description, responses.get("success", "Reload is a success!"),
                                    responses.get("failure", "Reload failed..."), guild_id, command_defs)


def register_static_command(client, name, description, message, guild_id):
    @client.tree.command(name=name, description=description, guild=guild_id)
    async def static_cmd(interaction: discord.Interaction):
        print(f"Command '/{name}' by '{interaction.user.display_name}' ({interaction.user.id})")

        await interaction.response.send_message(message)


def register_random_command(client, name, description, messages, guild_id):
    @client.tree.command(name=name, description=description, guild=guild_id)
    async def random_cmd(interaction: discord.Interaction):
        print(f"Command '/{name}' by '{interaction.user.display_name}' ({interaction.user.id})")

        response = random.choice(messages) if messages else "[No responses configured]"
        await interaction.response.send_message(response)


def register_reload_command(client, name, description, success, failure, guild_id, command_defs):
    @client.tree.command(name=name, description=description, guild=guild_id)
    async def reload_cmd(interaction: discord.Interaction):
        print(f"Command '/{name}' by '{interaction.user.display_name}' ({interaction.user.id})")

        await interaction.response.defer(ephemeral=True)

        try:
            await load_commands(client, command_defs, guild_id)
            await client.tree.sync(guild=guild_id)
            await interaction.followup.send(success)
        except Exception as e:
            print(f"[ERROR] Reload failed: {e}")
            await interaction.followup.send(failure)
