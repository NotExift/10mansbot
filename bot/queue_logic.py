import discord
from discord.ui import Button, View
from discord import Guild
import time
from datetime import datetime, timedelta, timezone
import asyncio
import os
from game_logic import start_match
import init


class joinQueueButton(Button):
    def __init__(self):
        super().__init__(label="Join Queue", style=discord.ButtonStyle.green)

    async def callback(self, interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user in init.QUEUE:
            await interaction.followup.send(
                "You are already in the queue.", ephemeral=True
            )
        else:
            init.QUEUE.append(interaction.user)
            await interaction.followup.send(
                "You have joined the queue!", ephemeral=True
            )


class leaveQueueButton(Button):
    def __init__(self):
        super().__init__(label="Leave Queue", style=discord.ButtonStyle.red)

    async def callback(self, interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user in init.QUEUE:
            init.QUEUE.remove(interaction.user)
            await interaction.followup.send(
                "You have been removed from the queue!", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "You are cannot leave a queue you aren't in.", ephemeral=True
            )


class acceptMatchButton(Button):
    def __init__(self):
        super().__init__(label="Accept Match", style=discord.ButtonStyle.red)

    async def callback(self, interaction):
        global accepted
        await interaction.response.defer(ephemeral=True)

        if interaction.user in accepted:
            await interaction.followup.send(
                "You have already accepted this match.", ephemeral=True
            )
        else:
            accepted.append(interaction.user)
            await interaction.followup.send(
                "You have accepted the match!", ephemeral=True
            )


async def display_queue(ctx):
    previous_queue = []
    join_queue_view = View(timeout=None)
    join_queue_view.add_item(joinQueueButton())
    join_queue_view.add_item(leaveQueueButton())
    init.QUEUE_MSG = await init.QUEUE_CHANNEL.send(
        embed=discord.Embed(title="Queue now open", color=0x00FF00),
        view=join_queue_view,
    )

    queue_lock = asyncio.Lock()

    while True:
        if not init.QUEUE_OPEN:
            embed = discord.Embed(title="Queue is currently closed.", color=0x00FF00)
            if init.QUEUE_MSG:
                await init.QUEUE_MSG.delete()
            init.QUEUE_MSG = await init.QUEUE_CHANNEL.send(embed=embed)
            return  # Exit the function if queue is closed

        # Update queue display if it has changed
        async with queue_lock:
            curr_player_count = len(init.QUEUE)
            if curr_player_count != len(previous_queue):
                queue_display = "\n".join(
                    [init.format_username(user.name) for user in init.QUEUE]
                )
                embed = discord.Embed(
                    title="Current Queue", description=queue_display, color=0x00FF00
                )
                embed.set_footer(
                    text=f"Player count: {curr_player_count}/{str(init.PLAYER_COUNT)}"
                )
                if init.QUEUE_MSG:
                    await init.QUEUE_MSG.delete()
                init.QUEUE_MSG = await init.QUEUE_CHANNEL.send(
                    embed=embed, view=join_queue_view
                )
                previous_queue = list(init.QUEUE)

            if curr_player_count == init.PLAYER_COUNT and not init.GAME_ONGOING:
                await queue_pop(ctx)

        await asyncio.sleep(3)


async def queue_pop(ctx):
    global accepted, readyup_msg
    accepted = []
    accept_match_view = View()
    accept_match_view.add_item(acceptMatchButton())

    future_time = datetime.now(timezone.utc) + timedelta(seconds=init.ACCEPT_TIME)
    unix_timestamp = int(future_time.timestamp())

    # Permissions setup
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False), # Deny access to everyone
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True) # Ensure bot has access
    }

    for user in init.QUEUE:
        overwrites[user] = discord.PermissionOverwrite(read_messages=True) # Allow users in init.QUEUE access

    # Create private channel with overwrites
    init.MATCHROOM_CHANNEL = await ctx.guild.create_text_channel(
        name=f"matchroom-{init.MATCH_ID}",
        overwrites=overwrites
    )
    init.MATCH_ID += 1

    # Sending initial readyup_msg
    initial_embed = discord.Embed(title="Match Accept", color=0x00FF00)
    participants_field = []
    for user in init.QUEUE:
        participants_field.append(f"❌<@{user.id}>")
    initial_embed.add_field(
        name="👥 Participants",
        value="\n".join(participants_field),
        inline=True,
    )
    readyup_msg = await init.MATCHROOM_CHANNEL.send(
        content=f"0/{init.PLAYER_COUNT} players are ready. \nReady up before <t:{int(unix_timestamp)}:t>",
        embed = initial_embed,
        view=accept_match_view
    )
    
    # Match Notifications PM
    p_pop_msg = discord.Embed(
        title="Your match has popped!",
        description=f"You have {init.ACCEPT_TIME} seconds to accept!\n https://discord.com/channels/{init.GUILD_ID}/{init.MATCHROOM_CHANNEL.id}",
    )
    match_notifications_role = discord.utils.get(
        ctx.guild.roles, name="Match Notifications"
    )
    # Filter the players who have the "Match Notifications" role
    players_with_role = [
        player
        for player in init.QUEUE
        if match_notifications_role in player.roles
    ]
    # Send the embed message to each player with the "Match Notifications" role
    for player in players_with_role:
        try:
            await player.send(embed=p_pop_msg, view=accept_match_view)
        except Exception as e:
            print(f"Couldn't send message to {player.name}: {e}")
    
    await queue_pop_sound()
    start_time = time.time()
    while (
        any(player not in accepted for player in init.QUEUE)
        and (time.time() - start_time) < init.ACCEPT_TIME
    ):
        await update_readyup_msg(accepted, init.PLAYER_COUNT, unix_timestamp)
        await asyncio.sleep(1)

    await readyup_msg.edit(view=None)

    if all(player in accepted for player in init.QUEUE):
        await update_readyup_msg(accepted, init.PLAYER_COUNT, unix_timestamp)
        await start_match(ctx)
    else:
        init.QUEUE[:] = [
            player for player in init.QUEUE if player in accepted
        ]
        try:
            await init.MATCHROOM_CHANNEL.delete()
            print(f"Channel matchroom-{init.MATCH_ID} was deleted successfully!")
        except Exception as e:
            print(f"An error occurred: {e}\nChannel matchroom-{init.MATCH_ID} failed to be deleted!")


async def queue_pop_sound():
    source = discord.FFmpegPCMAudio(init.QUEUEPOP_MP3)
    v_client = await init.VOICE_CHANNEL.connect()
    v_client.play(source)
    while v_client.is_playing():
        await asyncio.sleep(1)
    await v_client.disconnect()


async def update_readyup_msg(accepted_users, total_users, unix_timestamp):
    global readyup_msg
    embed = discord.Embed(title="Match Accept", color=0x00FF00)
    participants_field = []
    for user in init.QUEUE:
        status = "✅" if user in accepted_users else "❌"
        participants_field.append(f"{status}<@{user.id}>")

    embed.add_field(
        name="👥 Participants",
        value="\n".join(participants_field),
        inline=True
    )

    if len(accepted_users) == total_users:
        content = f"{len(accepted_users)}/{total_users} have readied up!"
    else:
        content = f"{len(accepted_users)}/{total_users} players are ready. \nReady up before <t:{unix_timestamp}:t>"

    await readyup_msg.edit(
        content=content,
        embed=embed
    )
