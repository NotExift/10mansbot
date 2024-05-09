import discord
import init
from init import *
from discord.ext import commands
from steamlink import slink



@init.bot.tree.command(description="End the current 10 mans game")
async def endgame(ctx: discord.Interaction):
    # Check if the user is a captain or an admin
    if (
        ctx.user == init.TEAM1_CAP
        or ctx.user == init.TEAM2_CAP
        or "Admin" in [role.name for role in ctx.user.roles]
        or "captain" in [role.name for role in ctx.user.roles]
    ):
        init.GAME_ONGOING = False
        captain_role = discord.utils.get(ctx.guild.roles, name="captain")
        if init.TEAM1_CAP is not None:
            await init.TEAM1_CAP.remove_roles(captain_role)
            init.TEAM1_CAP = None
        if init.TEAM2_CAP is not None:
            await init.TEAM2_CAP.remove_roles(captain_role)
            init.TEAM2_CAP = None
        # Clear all users from the queue
        init.QUEUE.clear()
        init.TEAM1.clear()
        init.TEAM2.clear()
        await ctx.response.send_message("The game has ended.")
    else:
        await ctx.response.send_message(
            "You do not have permissions to end the game.", ephemeral=True
        )


@init.bot.tree.command(name="mappool", description="List the current loaded mappool")
async def mappool(ctx: discord.Interaction):
    mapimage = discord.File("bot/mapsimage.jpg")
    try:
        await ctx.response.send_message(file=mapimage)
    except Exception as e:
        await ctx.response.send_message(f"An error occurred: {e}", ephemeral=True)

@init.bot.tree.command(name="link", description="Link your steam account")
async def link(ctx: discord.Interaction, link: str):
    user = ctx.user.name
    userid = ctx.user.id
    await slink(user, userid)