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
            print("Not connected to any guilds.")

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
            description=f"{member.mention} has left the server...",
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

        roles_before = set(r.id for r in before.roles)
        roles_after = set(r.id for r in after.roles)

        for key in ["hero_role", "knight_role", "artificer_role"]:
            data = config.get(key, {})
            role_id = data.get("id")
            announce_id = data.get("channel")

            if not role_id or not announce_id:
                continue
            if role_id not in roles_before and role_id in roles_after:
                embed = discord.Embed(
                    title=f"A new {key.replace('_role', '').title()} supporter!",
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
                        f"**{key.replace('_role', '').title()}**"
                        f"supporter!"
                    )
