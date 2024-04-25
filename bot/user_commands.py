import discord
import init
from init import *
from discord.ext import commands
from steamlink import extract_steam64id, get_faceit, connection, cursor



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
    # Check if user already has an entry in the database
    check_query = "SELECT steamid FROM userinfo WHERE discorduserid = %s"
    cursor.execute(check_query, (userid,))
    result = cursor.fetchone()
    # Extract steamid using the given link
    steamid = extract_steam64id(link, STEAMAPIKEY)
    if not steamid:
        await ctx.response.send_message("Invalid Steam link provided.")
        return
    # Get faceit details
    elo, rank = get_faceit(steamid, FACEITAPIKEY)
    if result:
        # Update existing entry if user already has one
        update_query = "UPDATE userinfo SET steamid = %s, faceitelo = %s, faceitrank = %s WHERE discorduserid = %s"
        data = (steamid, elo, rank, userid)
        try:
            cursor.execute(update_query, data)
            connection.commit()
            await ctx.response.send_message(
                "Your Steam account has been updated successfully!", ephemeral=True
            )
        except Exception as e:
            await ctx.response.send_message(
                f"Database update error: {str(e)}", ephemeral=True
            )
    else:
        # Insert new entry if no existing entry found
        insert_query = "INSERT INTO userinfo (discorduserid, discordusername, steamid, faceitelo, faceitrank) VALUES (%s, %s, %s, %s, %s)"
        data = (userid, user, steamid, elo, rank)
        try:
            cursor.execute(insert_query, data)
            connection.commit()
            await ctx.response.send_message(
                "Steam Account Linked Successfully!", ephemeral=True
            )
        except Exception as e:
            await ctx.response.send_message(
                f"Database upload error: {str(e)}", ephemeral=True
            )
