import asyncio
import random
from datetime import datetime, timezone

import discord


def log_command(name, interaction):
    print(f"Command '/{name}' by '{interaction.user.display_name}' "
          f"({interaction.user.id}) "
          f"in {interaction.channel.name[2:]}")


async def bot_wait(interaction, thinking=True, ephemeral=False, min_wait=1, max_wait=3):
    await interaction.response.defer(thinking=thinking, ephemeral=ephemeral)
    await asyncio.sleep(random.uniform(min_wait, max_wait))


async def load_commands(client, command_defs, guild_id, config):
    client.tree.clear_commands(guild=guild_id)

    for cmd in command_defs:
        name = cmd.get("name")
        desc = cmd.get("description", "No description provided")
        ctype = cmd.get("type")

        if ctype == "static":
            register_static_command(client, name, desc,
                                    cmd.get("response", ""),
                                    guild_id)

        elif ctype == "random":
            register_random_command(client, name, desc,
                                    cmd.get("responses", []),
                                    guild_id)

        elif ctype == "action" and name == "reload":
            resp = cmd.get("response", {})
            register_reload_command(client, name, desc,
                                    resp.get("success", ""),
                                    resp.get("failure", ""),
                                    guild_id, command_defs, config)

        elif ctype == "auth" and name == "legit":
            resp = cmd.get("response", {})
            register_auth_command(client, name, desc, resp, guild_id,
                                  config.get("legit", {}), config)


def register_static_command(client, name, desc, message, guild_id):
    @client.tree.command(name=name, description=desc, guild=guild_id)
    async def static_cmd(interaction: discord.Interaction):
        log_command(name, interaction)

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return

        await bot_wait(interaction)

        msg = message.replace("%member%", member.mention)
        await interaction.followup.send(msg)


def register_random_command(client, name, desc, messages, guild_id):
    @client.tree.command(name=name, description=desc, guild=guild_id)
    async def random_cmd(interaction: discord.Interaction):
        log_command(name, interaction)

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return

        await bot_wait(interaction)

        msg = random.choice(messages) if messages else "_oh..._"
        await interaction.followup.send(msg.replace("%member%", member.mention))


def register_reload_command(client, name, desc, success, failure, guild_id, command_defs, config):
    @client.tree.command(name=name, description=desc, guild=guild_id)
    async def reload_cmd(interaction: discord.Interaction):
        log_command(name, interaction)

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return

        await bot_wait(interaction, ephemeral=True)

        try:
            await load_commands(client, command_defs, guild_id, config)
            await client.tree.sync(guild=guild_id)
            await interaction.followup.send(success)
        except Exception as e:
            print(f"[ERROR] Reload failed: {e}")
            await interaction.followup.send(failure)


def register_auth_command(client, name, desc, responses, guild_id, legit_cfg, config):
    @client.tree.command(name=name, description=desc, guild=guild_id)
    async def auth_cmd(interaction: discord.Interaction):
        log_command(name, interaction)

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return

        await bot_wait(interaction)

        role = interaction.guild.get_role(legit_cfg.get("give_role_id"))
        member_age = (datetime.now(timezone.utc) - member.joined_at).days if member.joined_at else 0
        account_age = (datetime.now(timezone.utc) - member.created_at).days if member.created_at else 0

        if role and role in member.roles:
            result = "existed"
            msg = random.choice(responses.get("exist", ["Oh %member%... you are already legit, **yay!**"]))
        elif member_age >= legit_cfg.get("member_age", 14) and account_age >= legit_cfg.get("account_age", 365):
            result = "success"
            msg = random.choice(responses.get("success", ["Hey %member%! **You seem legit!**"]))
            if role:
                try:
                    await member.add_roles(role)
                    print(f"Granted role '{role.name}' ({role.id}) to '{member.display_name}' ({member.id})")
                except discord.Forbidden:
                    print(f"[WARN] No permission to grant role '{role.name}' ({role.id})")
        else:
            result = "failure"
            msg = random.choice(responses.get("failure", ["_I don't know you %member%..._"]))

        await interaction.followup.send(msg.replace("%member%", member.mention))

        if result == "existed":
            return

        log_channel_id = config.get("log_channel_id")
        log_channel = client.get_channel(log_channel_id) if isinstance(log_channel_id, int) else None

        if log_channel:
            result_label = {
                "success": f"{role.name.title()} Role Granted",
                "failure": f"Not Eligible for {role.name.title()} Role",
            }.get(result, "_Something else happened..._")

            embed = discord.Embed(title="Legitimacy Check", color=discord.Color.green())
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.add_field(name="User ID", value=member.id, inline=False)
            embed.add_field(name="Result", value=result_label, inline=False)
            embed.add_field(name="Member Age", value=f"{member_age} days", inline=False)
            embed.add_field(name="Account Age", value=f"{account_age} days", inline=False)
            embed.timestamp = datetime.now(timezone.utc)

            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                print(f"[WARN] Cannot log legitimacy check for {member.id}")
