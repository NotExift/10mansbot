import discord
import init
from init import *
from discord.ext import commands
from steamlink import extract_steam64id, get_faceit, connection, cursor

@init.bot.tree.command(name="joinqueue", description="Join the 10 mans queue")
async def join(ctx: discord.Interaction):
    # Check if a game is ongoing
    if init.GAME_ONGOING:
        await ctx.response.send_message("A game is currently ongoing. Please wait until the game is over before joining the queue.", ephemeral=True)
    else:
        # Check if the user is already in the queue
        if ctx.user in init.QUEUE:
            await ctx.response.send_message("You are already in the queue.", ephemeral=True)
        else:
            if init.QUEUE_OPEN == False:
                await ctx.response.send_message("Queue is currently closed.", ephemeral=True)
            # Add the user to the queue based on the current size of the queues
            else:
                init.QUEUE.append(ctx.user)
                await ctx.response.send_message("You have joined the queue.", ephemeral=True)


@init.bot.tree.command(name="leavequeue", description="Leave the 10 mans queue")
async def leave(ctx: discord.Interaction):
    # Check if a game is ongoing
    if init.QUEUE_OPEN == False:
        await ctx.response.send_message("Queue is currently closed.", ephemeral=True)
    else:
        if init.GAME_ONGOING:
            await ctx.response.send_message("A game is currently ongoing. You cannot leave the queue until the game is over.", ephemeral=True)
        else:
            # Check if the user is in the queue
            if ctx.user in init.QUEUE:
                init.QUEUE.remove(ctx.user)
                await ctx.response.send_message("You have left the queue.", ephemeral=True)
            else:
                await ctx.response.send_message("You are not in the queue.", ephemeral=True)

@init.bot.tree.command(description="End the current 10 mans game")
async def endgame(ctx: discord.Interaction):
    # Check if the user is a captain or an admin
    if ctx.user == init.TEAM1_CAP or ctx.user == init.TEAM2_CAP or "Admin" in [role.name for role in ctx.user.roles] or "captain" in [role.name for role in ctx.user.roles]:
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
        await ctx.response.send_message("You do not have permissions to end the game.", ephemeral=True)

@init.bot.tree.command(name="mappool", description="List the current loaded mappool")
async def mappool(ctx: discord.Interaction):
    mapimage = discord.File("bot/mapsimage.jpg")
    try:
        await ctx.response.send_message(file= mapimage)
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
            await ctx.response.send_message("Your Steam account has been updated successfully!", ephemeral=True)
        except Exception as e:
            await ctx.response.send_message(f"Database update error: {str(e)}", ephemeral=True)
    else:
        # Insert new entry if no existing entry found
        insert_query = "INSERT INTO userinfo (discorduserid, discordusername, steamid, faceitelo, faceitrank) VALUES (%s, %s, %s, %s, %s)"
        data = (userid, user, steamid, elo, rank)
        try:
            cursor.execute(insert_query, data)
            connection.commit()
            await ctx.response.send_message("Steam Account Linked Successfully!", ephemeral=True)
        except Exception as e:
            await ctx.response.send_message(f"Database upload error: {str(e)}", ephemeral=True)
