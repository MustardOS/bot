import discord
from discord.utils import utcnow


def is_ignored(channel, ignore_channel):
    return channel and channel.id in ignore_channel


def register(client, config):
    ignore_channel = set(config.get("ignored_channels", []))
    log_channel_id = config.get("log_channel_id")

    @client.event
    async def on_ready():
        print(f"Logged in as '{client.user}' ({client.user.id})")
        if client.guilds:
            guild = client.guilds[0]
            print(f"Connected to: '{guild.name}' ({guild.id})")
        else:
            print("Not connected to any guilds...")

    @client.event
    async def on_message(message):
        if message.author.bot:
            return

        if message.content.startswith("/"):
            return

        spam_attachment_block = config.get("spam_attachment_block")
        legit_role_id = config.get("legit", {}).get("give_role_id")

        if spam_attachment_block and any(role.id == spam_attachment_block for role in message.author.roles):
            if legit_role_id and any(role.id == legit_role_id for role in message.author.roles):
                return

            if not message.content.strip() and message.attachments:
                await message.delete()

                if message.author.bot or is_ignored(message.channel, ignore_channel):
                    return

                log = client.get_channel(log_channel_id)
                if not log:
                    return

                embed = discord.Embed(title="Attachment Spam Blocked", color=discord.Color.blurple())
                embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
                embed.add_field(name="User ID", value=message.author.id, inline=False)
                embed.add_field(name="Channel", value=message.channel.name[2:], inline=False)
                embed.timestamp = message.created_at

                await log.send(embed=embed)

    @client.event
    async def on_message_delete(message):
        if message.author.bot or is_ignored(message.channel, ignore_channel):
            return

        log = client.get_channel(log_channel_id)

        if not log:
            return

        embed = discord.Embed(title="Message Deleted", color=discord.Color.red())
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)

        embed.add_field(name="User ID", value=message.author.id, inline=False)
        embed.add_field(name="Channel", value=message.channel.name[2:], inline=False)
        embed.add_field(name="Message", value=message.content or "*[nothing]*", inline=False)

        if message.attachments:
            urls = "\n".join(att.url for att in message.attachments)
            embed.add_field(name="Attachments", value=urls, inline=False)

        embed.timestamp = message.created_at
        await log.send(embed=embed)

    @client.event
    async def on_message_edit(before, after):
        if before.author.bot or is_ignored(before.channel, ignore_channel):
            return
        if before.content == after.content and before.attachments == after.attachments:
            return
        log = client.get_channel(log_channel_id)

        if not log:
            return

        embed = discord.Embed(title="Message Edited", color=discord.Color.orange())
        embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)

        embed.add_field(name="User ID", value=before.author.id, inline=False)
        embed.add_field(name="Channel", value=before.channel.name[2:], inline=False)
        embed.add_field(name="Before", value=before.content or "*[nothing]*", inline=False)
        embed.add_field(name="After", value=after.content or "*[nothing]*", inline=False)

        if after.attachments:
            urls = "\n".join(att.url for att in after.attachments)
            embed.add_field(name="Attachments", value=urls, inline=False)

        embed.timestamp = after.edited_at or utcnow()
        await log.send(embed=embed)

    @client.event
    async def on_member_remove(member):
        log = client.get_channel(log_channel_id)

        if not log:
            return

        embed = discord.Embed(
            title="Member Left",
            color=discord.Color.dark_red()
        )

        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(name="User ID", value=member.id, inline=False)

        if member.joined_at:
            embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)

        embed.timestamp = utcnow()
        await log.send(embed=embed)

    @client.event
    async def on_member_update(before, after):
        log = client.get_channel(log_channel_id)

        if not log:
            return

        new_roles = set(r.id for r in after.roles) - set(r.id for r in before.roles)

        roles_config = config.get("announce_roles", {})
        role_priority = roles_config.get("priority", [])

        for key in role_priority:
            role_data = roles_config.get(key, {})
            role_id = role_data.get("id")
            announce_id = role_data.get("channel")

            if not role_id or not announce_id:
                continue

            if role_id in new_roles:
                embed = discord.Embed(
                    title=f"A new {key.title()} supporter!",
                    color=discord.Color.gold()
                )

                embed.set_author(name=str(after), icon_url=after.display_avatar.url)

                embed.add_field(name="User ID", value=after.id, inline=False)

                embed.timestamp = utcnow()
                await log.send(embed=embed)

                announce = client.get_channel(announce_id)
                if announce:
                    await announce.send(
                        f"## 🎉 {after.mention} is now a "
                        f"**{key.title()}** "
                        f"supporter!"
                    )
                break
