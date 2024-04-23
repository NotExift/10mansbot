import discord
from discord.ext import commands
import asyncio
import init
from queue_logic import display_queue
from game_logic import change_map

@init.bot.tree.command(name="openqueue")
async def open_queue(ctx: discord.Interaction):
    global queue_task
    if "Admin" in [role.name for role in ctx.user.roles]:  # Replace "Admin" with your actual admin role name
        init.QUEUE_OPEN = True
        queue_task = asyncio.create_task(display_queue(ctx))
        await ctx.response.send_message("Queue is now open. Players can join!")
    else:
        await ctx.response.send_message("You do not have permissions to open the queue.", ephemeral=True)

@init.bot.tree.command(name="closequeue")
async def close_queue(ctx: discord.Interaction):
    global queue_task
    if "Admin" in [role.name for role in ctx.user.roles] and init.QUEUE_OPEN == True:  # Replace "Admin" with your actual admin role name
        init.QUEUE_OPEN = False
        queue_task.cancel()
        embed = discord.Embed(title="Queue is currently closed.", color=0x00ff00)
        if init.QUEUE_MSG:
            await init.QUEUE_MSG.delete()
        await init.QUEUE_CHANNEL.send(embed=embed)
        try:
            init.QUEUE.clear()
            print("Queue clear success!")
            init.TEAM1.clear()
            init.TEAM2.clear()
        except:
            print("Queue clear failure!")
        await ctx.response.send_message("Queue is now closed.")
    elif init.QUEUE_OPEN == False:
        await ctx.response.send_message("Queue is already closed.", ephemeral=True)
    else:
        await ctx.response.send_message("You do not have permissions to close the queue.", ephemeral=True)

@init.bot.tree.command(name="wingmanmode", description="Toggle Wingman Mode (2v2)")
async def wingmanmode(ctx: discord.Interaction, enabled: bool):
    if "Admin" in [role.name for role in ctx.user.roles]:
        if enabled:
            init.TEAM_SIZE = 2
            init.PLAYER_COUNT = 4
        else:
            init.TEAM_SIZE = 5
            init.PLAYER_COUNT = 10
        await ctx.response.send_message(f"Wingman mode has been {'enabled' if enabled else 'disabled'}.", ephemeral=True)
    else:
        await ctx.response.send_message("You do not have the required permissions to perform this action.", ephemeral=True)

''' ================================================== TEST COMMANDS ================================================== '''

@init.bot.tree.command(name="changemap", description="Test the RCON changemap")
async def changemap(ctx: discord.Interaction, map: str):
    if "Admin" not in [role.name for role in ctx.user.roles]:
        await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await change_map(map)
    await ctx.response.send_message(f"Changing map to {map}.", ephemeral=True)

@init.bot.tree.command(name="addplayer", description="Manually add a player to the queue")
async def add_player(ctx: discord.Interaction, name: discord.Member):
    if "Admin" not in [role.name for role in ctx.user.roles]:
        await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    user = name
    if user:
        if user not in init.QUEUE:
            init.QUEUE.append(user)
            await ctx.response.send_message(f"{user.name} has been added to the queue.", ephemeral=True)
        else:
            await ctx.response.send_message("This user is already in the queue.", ephemeral=True)
    else:
        await ctx.response.send_message("No user found with that name in this server.", ephemeral=True)

@init.bot.tree.command(name="removeplayer", description="Manually remove a player from the queue")
async def remove_player(ctx: discord.Interaction, name: discord.Member):
    if "Admin" not in [role.name for role in ctx.user.roles]:
        await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    user = name
    if user:
        if user in init.QUEUE:
            init.QUEUE.remove(user)
            await ctx.response.send_message(f"{user.name} has been removed from the queue.", ephemeral=True)
        else:
            await ctx.response.send_message("This user is not in the queue.", ephemeral=True)
    else:
        await ctx.response.send_message("No user found with that name in this server.", ephemeral=True)

@init.bot.tree.command(name="setcaptains", description="Manually set captains")
async def setcaptains(ctx: discord.Interaction, captain1: discord.Member, captain2: discord.Member):
    if "Admin" not in [role.name for role in ctx.user.roles]:
        await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    init.TEAM1_CAP = captain1
    init.TEAM2_CAP = captain2
    await ctx.response.send_message(f"Set {captain1} and {captain2} as captains", ephemeral=True)

@init.bot.tree.command(name="clearcaptains", description="clear out the manually set captains")
async def clearcaptains(ctx:discord.Interaction):
    if "Admin" not in [role.name for role in ctx.user.roles]:
        await ctx.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    init.TEAM1_CAP, init.TEAM2_CAP = None
    await ctx.response.send_message(f"Cleared manually set captains", ephemeral=True)