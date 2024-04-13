import discord
from discord.ext import commands
from discord import app_commands
import random
from valve.rcon import RCON
import asyncio
import configparser
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
# Create a bot instance
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

#bot command sync
@bot.event
async def on_ready():
    global ban_channel, pick_channel, channel, game_channel_id, SERVER_IP, SERVER_PORT, RCON_PASSWORD
    #initialize serverinfo
    ban_channel = bot.get_channel(int(os.getenv("BAN_CHANNEL")))
    pick_channel = bot.get_channel(int(os.getenv("PICK_CHANNEL")))
    channel = bot.get_channel(int(os.getenv("QUEUE_CHANNEL")))
    game_channel_id = os.getenv("GAMELOG_CHANNEL")
    SERVER_IP = os.getenv("SERVER_IP")
    SERVER_PORT = os.getenv("SERVER_PORT")
    RCON_PASSWORD = os.getenv("RCON_PASSWORD")
    API_KEY = os.getenv("API_KEY")
    print("Bot is ready!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands(s)")
    except Exception as e:
        print(e)

# Initialize queues for each team
queue = []
queue_message = None
game_ongoing = False
team1_captain = None
team2_captain = None
team1 = None
team2 = None

maps = configparser.ConfigParser()
maps.read('maps.cfg')
categories = list(maps.sections())
map_ids = {}
for category in maps.sections():
    for map_name, map_id in maps.items(category):
        map_ids[map_name] = map_id

def format_username(username):
    return username.replace("_", "\_")
    
async def display_queue(ctx):
    global queue_message, game_ongoing, team1_captain, team2_captain, team1, team2
    previous_queue = []
    queue_message = await channel.send(embed=discord.Embed(title="Queue now open", color=0x00ff00))
    while True:
        if not queue_open:
            embed = discord.Embed(title="Queue is currently closed.", color=0x00ff00)
            if queue_message:
                await queue_message.delete()
            queue_message = await channel.send(embed=embed)
            return  # Exit the function if queue is closed

        # Update queue display if it has changed
        player_count = len(queue)
        if player_count != len(previous_queue):
            queue_display = '\n'.join([format_username(user.name) for user in queue])
            embed = discord.Embed(title="Current Queue", description=queue_display, color=0x00ff00)
            embed.set_footer(text=f"Player count: {player_count}/10")
            if queue_message:
                await queue_message.delete()
            queue_message = await channel.send(embed=embed)
            previous_queue = list(queue)

        if player_count == 10 and not game_ongoing:
            game_ongoing = True
            team1_captain, team2_captain = random.sample(queue, 2)  # Select two random captains
            captain_role = discord.utils.get(ctx.guild.roles, name="captain")
            await team1_captain.add_roles(captain_role)
            await team2_captain.add_roles(captain_role)
            team1, team2 = await pick_players(team1_captain, team2_captain, queue, pick_channel)  # Captains pick players in pick_channel
            embed = discord.Embed(title="Game Ongoing", color=0x00ff00)
            embed.add_field(name="Team 1", value='\n'.join([user.name for user in team1]), inline=True)
            embed.add_field(name="Team 2", value='\n'.join([user.name for user in team2]), inline=True)
            embed.set_footer(text=f"Captains: {team1_captain.name}, {team2_captain.name}")
            if queue_message:  # If there is a previous message, delete it
                await queue_message.delete()
            queue_message = await channel.send(embed=embed)
            try:
                await start_map_ban(ctx, team1_captain, team2_captain, channel, team1, team2)  # Assuming start_map_ban uses the channel for communication
            except Exception as e:
                print(f"Error in start_map_ban: {e}")
        await asyncio.sleep(3)  

async def pick_players(team1_captain, team2_captain, players, channel):
    global team1
    global team2
    team1 = [team1_captain]
    team2 = [team2_captain]
    while len(team1) < 5 or len(team2) < 5:
        if len(team1) < 5:
            await channel.send(f"{team1_captain.mention}, please pick a player: {', '.join([player.name for player in players if player not in team1 and player not in team2])}")
            player_pick = await bot.wait_for('message', check=lambda m: m.author == team1_captain and m.content in [player.name for player in players])
            picked_player = next(player for player in players if player.name == player_pick.content)
            team1.append(picked_player)
        if len(team2) < 5:
            await channel.send(f"{team2_captain.mention}, please pick a player: {', '.join([player.name for player in players if player not in team1 and player not in team2])}")
            player_pick = await bot.wait_for('message', check=lambda m: m.author == team2_captain and m.content in [player.name for player in players])
            picked_player = next(player for player in players if player.name == player_pick.content)
            team2.append(picked_player)
    return team1, team2

@bot.tree.command(description="End the current 10 mans game")
async def endgame(ctx: discord.Interaction):
    global game_ongoing
    global team1_captain
    global team2_captain
    global queue
    global team1
    global team2
    # Check if the user is a captain or an admin
    if ctx.user == team1_captain or ctx.user == team2_captain or "Admin" in [role.name for role in ctx.user.roles] or "captain" in [role.name for role in ctx.user.roles]:
        game_ongoing = False
        captain_role = discord.utils.get(ctx.guild.roles, name="captain")
        if team1_captain is not None:
            await team1_captain.remove_roles(captain_role)
            team1_captain = None
        if team2_captain is not None:
            await team2_captain.remove_roles(captain_role)
            team2_captain = None
        # Clear all users from the queue
        queue.clear()
        team1.clear()
        team2.clear()
        await ctx.response.send_message("The game has ended.")
    else:
        await ctx.response.send_message("You do not have permissions to end the game.", ephemeral=True)

@bot.tree.command(name="openqueue")
async def open_queue(ctx: discord.Interaction):
    global queue_open, channel
    global queue_task
    if "Admin" in [role.name for role in ctx.user.roles]:  # Replace "Admin" with your actual admin role name
        queue_open = True
        queue_task = asyncio.create_task(display_queue(ctx))
        await ctx.channel.send("Queue is now open. Players can join!")
        await ctx.response.send_message(f"Current settings are {SERVER_IP}:{SERVER_PORT}", ephemeral=True)

    else:
        await ctx.response.send_message("You do not have permissions to open the queue.", ephemeral=True)

@bot.tree.command(name="closequeue")
async def close_queue(ctx: discord.Interaction):
    global queue
    global team1
    global team2
    global queue_open
    global queue_task
    if "Admin" in [role.name for role in ctx.user.roles] and queue_open == True:  # Replace "Admin" with your actual admin role name
        queue_open = False
        queue_task.cancel()
        try:
            queue.clear()
            print("queue clear success")
            team1.clear()
            team2.clear()
        except:
            print("failed")
        await ctx.response.send_message("Queue is now closed.")
    elif queue_open == False:
        await ctx.response.send_message("Queue is already closed.", ephemeral=True)
    else:
        await ctx.response.send_message("You do not have permissions to close the queue.", ephemeral=True)

# Command to join the queue
@bot.tree.command(name="joinqueue", description="Join the 10 mans queue")
async def join(ctx: discord.Interaction):
    global game_ongoing
    # Check if a game is ongoing
    if game_ongoing:
        await ctx.response.send_message("A game is currently ongoing. Please wait until the game is over before joining the queue.", ephemeral=True)
    else:
        # Check if the user is already in the queue
        if ctx.user in queue:
            await ctx.response.send_message("You are already in the queue.", ephemeral=True)
        else:
            if queue_open == False:
                await ctx.response.send_message("Queue is currently closed.", ephemeral=True)
            # Add the user to the queue based on the current size of the queues
            else:
                queue.append(ctx.user)
                await ctx.response.send_message("You have joined the queue.", ephemeral=True)

# Command to leave the queue
@bot.tree.command(name="leavequeue", description="Leave the 10 mans queue")
async def leave(ctx: discord.Interaction):
    global game_ongoing
    # Check if a game is ongoing
    if queue_open == False:
        await ctx.response.send_message("Queue is currently closed.", ephemeral=True)
    else:
        if game_ongoing:
            await ctx.response.send_message("A game is currently ongoing. You cannot leave the queue until the game is over.", ephemeral=True)
        else:
            # Check if the user is in the queue
            if ctx.user in queue:
                queue.remove(ctx.user)
                await ctx.response.send_message("You have left the queue.", ephemeral=True)
            else:
                await ctx.response.send_message("You are not in the queue.", ephemeral=True)

async def ban_category(captain, categories, ban_channel):
    global game_ongoing
    while True:
        await asyncio.sleep(0)  # Yield control to the event loop
        if not game_ongoing:
            return
        # Prompt the captain to ban a category
        await ban_channel.send(f"{captain.mention}, please ban a category: {', '.join(categories)}")
        category_ban = await bot.wait_for('message', check=lambda m: m.author == captain and m.content in categories)
        categories.remove(category_ban.content)
        return categories

async def ban_map(captain, maps, ban_channel):
    global game_ongoing
    while True:
        await asyncio.sleep(0)  # Yield control to the event loop
        if not game_ongoing:
            return
    # Prompt the captain to ban a map
        await ban_channel.send(f"{captain.mention}, please ban a map: {', '.join(maps)}")
        map_ban = await bot.wait_for('message', check=lambda m: m.author == captain and m.content in maps)
        maps.remove(map_ban.content)
        return maps

async def start_map_ban(ctx, captain1, captain2, ban_channel, team1, team2):
    global categories
    global game_ongoing
    game_channel = bot.get_channel(game_channel_id)
    await ban_channel.send("Map List\nhttps://imgur.com/a/4a5HkAq")
    while len(categories) > 1:
        if not game_ongoing:
            return
        categories = await ban_category(captain1, categories, ban_channel)
        if len(categories) > 1:
            categories = await ban_category(captain2, categories, ban_channel)
    map_list = list(maps.options(categories[0]))
    while len(map_list) > 1:
        if not game_ongoing:
            return
        map_list = await ban_map(captain1, map_list, ban_channel)
        if len(map_list) > 1:
            map_list = await ban_map(captain2, map_list, ban_channel)
    if game_ongoing:
        await ban_channel.send(f"The final map is: {map_list[0]}\n Reminder that one of the captains should /endgame after the game is over for the queue to reopen!")
        current_date_time = datetime.datetime.now().strftime("%B %d, %Y, %H:%M:%S")
        # Create the embed message
        embed = discord.Embed(title=f"Game: {current_date_time}", color=0x00ff00)
        embed.add_field(name="Map", value=map_list[0], inline=False)
        embed.add_field(name="Team 1", value='\n'.join([f'<@{user.id}>' for user in team1]), inline=True)
        embed.add_field(name="Team 2", value='\n'.join([f'<@{user.id}>' for user in team2]), inline=True)
        embed.set_footer(text=f"connect {SERVER_PORT}:{SERVER_IP}; password okkkkkkk")
        # Send the embed message to the game channel
        await game_channel.send(embed=embed)
        # Create a new embed message for the players
        player_embed = discord.Embed(title="Your game is ready! The server may take a minute before switching maps, please be patient.", color=0x00ff00)
        player_embed.add_field(name="Map", value=map_list[0], inline=False)
        player_embed.add_field(name="Team 1", value='\n'.join([f'<@{user.id}>' for user in team1]), inline=True)
        player_embed.add_field(name="Team 2", value='\n'.join([f'<@{user.id}>' for user in team2]), inline=True)
        player_embed.set_footer(text=f"connect {SERVER_IP}:{SERVER_PORT}; password okkkkkkk")
        # Get the role object for "Match Notifications"
        match_notifications_role = discord.utils.get(ctx.guild.roles, name="Match Notifications")
        # Filter the players who have the "Match Notifications" role
        players_with_role = [player for player in team1 + team2 if match_notifications_role in player.roles]
        # Send the embed message to each player with the "Match Notifications" role
        for player in players_with_role:
            try:
                await player.send(embed=player_embed)
            except Exception as e:
                print(f"Couldn't send message to {player.name}: {e}")
        # Create a valve rcon connection to the counterstrike server
        with RCON((SERVER_IP, int(SERVER_PORT)), RCON_PASSWORD) as rcon:
            # Send the command wsmap <mapid>
            rcon.execute(f'css_say Map changing...')
            rcon.execute(f'css_wsmap {map_ids[map_list[0]]}')

# Initialize queue status
queue_open = False

# Run the bot with your token
bot.run(API_KEY)
