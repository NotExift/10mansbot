import discord
import init
from init import *
from discord.ext import commands


@init.bot.tree.command(name="mappool", description="List the current loaded mappool")
async def mappool(ctx: discord.Interaction):
    mapimage = discord.File("bot/mapsimage.jpg")
    try:
        await ctx.response.send_message(file=mapimage)
    except Exception as e:
        await ctx.response.send_message(f"An error occurred: {e}", ephemeral=True)
