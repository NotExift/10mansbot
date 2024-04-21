import discord
from discord.ext import commands
from init import *

@bot.tree.command(name="joinqueue", description="Join the 10 mans queue")
async def join(ctx: discord.Interaction):
    # Check if a game is ongoing
    if GAME_ONGOING:
        await ctx.response.send_message("A game is currently ongoing. Please wait until the game is over before joining the queue.", ephemeral=True)
    else:
        # Check if the user is already in the queue
        if ctx.user in QUEUE:
            await ctx.response.send_message("You are already in the queue.", ephemeral=True)
        else:
            if QUEUE_OPEN == False:
                await ctx.response.send_message("Queue is currently closed.", ephemeral=True)
            # Add the user to the queue based on the current size of the queues
            else:
                QUEUE.append(ctx.user)
                await ctx.response.send_message("You have joined the queue.", ephemeral=True)


@bot.tree.command(name="leavequeue", description="Leave the 10 mans queue")
async def leave(ctx: discord.Interaction):
    # Check if a game is ongoing
    if QUEUE_OPEN == False:
        await ctx.response.send_message("Queue is currently closed.", ephemeral=True)
    else:
        if GAME_ONGOING:
            await ctx.response.send_message("A game is currently ongoing. You cannot leave the queue until the game is over.", ephemeral=True)
        else:
            # Check if the user is in the queue
            if ctx.user in QUEUE:
                QUEUE.remove(ctx.user)
                await ctx.response.send_message("You have left the queue.", ephemeral=True)
            else:
                await ctx.response.send_message("You are not in the queue.", ephemeral=True)