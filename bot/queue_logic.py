import discord
from discord.ui import Button, View
import time
import asyncio
from game_logic import start_match
import init

class joinQueueButton(Button):
    def __init__(self):
        super().__init__(label="Join Queue", style=discord.ButtonStyle.green)

    async def callback(self, interaction):
        if interaction.user in init.QUEUE:
            await interaction.response.send_message("You are already in the queue.", ephemeral=True)
        else:
            init.QUEUE.append(interaction.user)

class acceptMatchButton(Button):
    def __init__(self):
        super().__init__(label="Accept Match", style=discord.ButtonStyle.red)

    async def callback(self, interaction):
        global accepted
        if interaction.user in accepted:
            await interaction.response.send_message("You have already accepted this match.", ephemeral=True)
        else:
            accepted.append(interaction.user)

async def display_queue(ctx):
    previous_queue = []
    init.QUEUE_MSG = await init.QUEUE_CHANNEL.send(embed=discord.Embed(title="Queue now open", color=0x00ff00))
    while True:
        if not init.QUEUE_OPEN:
            embed = discord.Embed(title="Queue is currently closed.", color=0x00ff00)
            if init.QUEUE_MSG:
                await init.QUEUE_MSG.delete()
            init.QUEUE_MSG = await init.QUEUE_CHANNEL.send(embed=embed)
            return  # Exit the function if queue is closed

        # Update queue display if it has changed
        curr_player_count = len(init.QUEUE)
        if curr_player_count != len(previous_queue):
            queue_display = '\n'.join([init.format_username(user.name) for user in init.QUEUE])
            embed = discord.Embed(title="Current Queue", description=queue_display, color=0x00ff00)
            embed.set_footer(text=f"Player count: {curr_player_count}/{str(init.PLAYER_COUNT)}")
            if init.QUEUE_MSG:
                await init.QUEUE_MSG.delete()
            init.QUEUE_MSG = await init.QUEUE_CHANNEL.send(embed=embed)
            previous_queue = list(init.QUEUE)

        if curr_player_count == init.PLAYER_COUNT and not init.GAME_ONGOING:
            # Match accept system
            global accepted
            accepted = []
            start_time = time.time()
            queue_pop_sound()

            while accepted.sort() != init.QUEUE.sort() or time.time() - start_time < init.ACCEPT_TIME:
                continue

            if accepted.sort() == init.QUEUE.sort():
                start_match(ctx)
            else:
                for player in init.QUEUE:
                    if player not in accepted:
                        init.QUEUE.remove(player)
            
        await asyncio.sleep(3)

async def queue_pop_sound():
    source = discord.FFmpegPCMAudio(init.QUEUEPOP_MP3)
    v_client = await init.VOICE_CHANNEL.connect()
    v_client.play(source)
    while v_client.is_playing():
        await asyncio.sleep(1)
    await v_client.disconnect()