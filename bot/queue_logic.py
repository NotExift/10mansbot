import discord
from discord.ui import Button, View
import time
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
    join_queue_view = View()
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
                # Match accept system
                global accepted
                accepted = []
                accept_match_view = View()
                accept_match_view.add_item(acceptMatchButton())
                await init.QUEUE_MSG.edit(view=accept_match_view)
                qchan = os.getenv("QUEUE_CHANNEL")
                popmsg = discord.Embed(
                    title="Your match has popped!",
                    description=f"You have 30 seconds to accept!\n https://discord.com/channels/{init.GUILD_ID}/{qchan}",
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
                        await player.send(embed=popmsg, view=accept_match_view)
                    except Exception as e:
                        print(f"Couldn't send message to {player.name}: {e}")
                await queue_pop_sound()
                start_time = time.time()
                while (
                    any(player not in accepted for player in init.QUEUE)
                    and (time.time() - start_time) < init.ACCEPT_TIME
                ):
                    await init.QUEUE_MSG.edit(
                        content=f"You have {init.ACCEPT_TIME - round(time.time()-start_time)}s left to accept if you haven't already!"
                    )
                    await asyncio.sleep(1)

                await init.QUEUE_MSG.edit(view=None)

                if all(player in accepted for player in init.QUEUE):
                    await start_match(ctx)
                else:
                    init.QUEUE[:] = [
                        player for player in init.QUEUE if player in accepted
                    ]

        await asyncio.sleep(3)


async def queue_pop_sound():
    source = discord.FFmpegPCMAudio(init.QUEUEPOP_MP3)
    v_client = await init.VOICE_CHANNEL.connect()
    v_client.play(source)
    while v_client.is_playing():
        await asyncio.sleep(1)
    await v_client.disconnect()
