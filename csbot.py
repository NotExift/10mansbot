import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import random
from valve.rcon import RCON
import asyncio
import configparser
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# Global Variables
PLAYER_COUNT = 10
TEAM_SIZE = 5
SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = os.getenv("SERVER_PORT")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

# Create a bot instance
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

ban_channel = None
pick_channel = None
channel = None
game_channel = None

queue = []
queue_message = None
queue_open = False
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

# Event
@bot.event
async def on_ready():
    global ban_channel, pick_channel, channel, game_channel
    ban_channel = bot.get_channel(int(os.getenv("BAN_CHANNEL")))
    pick_channel = bot.get_channel(int(os.getenv("PICK_CHANNEL")))
    channel = bot.get_channel(int(os.getenv("QUEUE_CHANNEL")))
    game_channel = bot.get_channel(int(os.getenv("GAMELOG_CHANNEL")))
    print("Bot is ready!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands(s)")
    except Exception as e:
        print(e)

''' ================================================== BOT COMMANDS ================================================== '''

@bot.tree.command(description="End the current 10 mans game")
async def endgame(ctx: discord.Interaction):
    global game_ongoing, team1_captain, team2_captain, queue, team1, team2

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
    global queue_open, queue_task, channel
    if "Admin" in [role.name for role in ctx.user.roles]:  # Replace "Admin" with your actual admin role name
        queue_open = True
        queue_task = asyncio.create_task(display_queue(ctx))
        await ctx.response.send_message("Queue is now open. Players can join!")
    else:
        await ctx.response.send_message("You do not have permissions to open the queue.", ephemeral=True)

@bot.tree.command(name="closequeue")
async def close_queue(ctx: discord.Interaction):
    global queue, queue_open, queue_task, team1, team2
    if "Admin" in [role.name for role in ctx.user.roles] and queue_open == True:  # Replace "Admin" with your actual admin role name
        queue_open = False
        queue_task.cancel()
        embed = discord.Embed(title="Queue is currently closed.", color=0x00ff00)
        if queue_message:
            await queue_message.delete()
        await channel.send(embed=embed)
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
            embed.set_footer(text=f"Player count: {player_count}/{str(PLAYER_COUNT)}")
            if queue_message:
                await queue_message.delete()
            queue_message = await channel.send(embed=embed)
            previous_queue = list(queue)

        if player_count == PLAYER_COUNT and not game_ongoing:
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
                await start_map_ban(ctx, team1_captain, team2_captain, ban_channel, team1, team2)  # Assuming start_map_ban uses the channel for communication
            except Exception as e:
                print(f"Error in start_map_ban: {e}")
        await asyncio.sleep(3)  

''' ================================================== PLAYER PICK ================================================== '''

class playerButton(Button):
    def __init__(self, player):
        super().__init__(label=player.name, style=discord.ButtonStyle.green)
        self.player = player
    
    async def callback(self, interaction):
        global current_cap, team1_captain, team2_captain, team1, team2

        if interaction.user == current_cap:
            if current_cap == team1_captain and len(team1) < TEAM_SIZE:
                team1.append(self.player)
                current_cap = team2_captain
            elif current_cap == team2_captain and len(team2) < TEAM_SIZE:
                team2.append(self.player)
                current_cap = team1_captain

            # Remove this button from the view
            player_button_menu.remove_item(self)

            player_picks_embed.clear_fields()
            player_picks_embed.add_field(name="Team 1", value='\n'.join([f'<@{user.id}>' for user in team1]), inline=True)
            player_picks_embed.add_field(name="Team 2", value='\n'.join([f'<@{user.id}>' for user in team2]), inline=True)

            await interaction.message.edit(content=f"{current_cap.mention} please select a player!", embed=player_picks_embed, view=player_button_menu)
        else:
            await interaction.response.send_message("It is either not your turn, or you are not allowed to make a selection.", ephemeral=True)

async def pick_players(team1_captain, team2_captain, players, channel):
    global team1, team2, current_cap, player_button_menu, player_picks_embed
    team1 = [team1_captain]
    team2 = [team2_captain]
    current_cap = team1_captain

    player_button_menu = View()
    for player in players:
        if player != team1_captain and player != team2_captain:
            player_button_menu.add_item(playerButton(player))

    player_picks_embed = discord.Embed(title="Player Picks", color=0x00ff00)
    player_picks_embed.add_field(name="Team 1", value='\n'.join([f'<@{user.id}>' for user in team1]), inline=True)
    player_picks_embed.add_field(name="Team 2", value='\n'.join([f'<@{user.id}>' for user in team2]), inline=True)

    picks_msg = await channel.send(content=f"{current_cap.mention} please select a player!", embed=player_picks_embed, view=player_button_menu)

    while len(team1) < TEAM_SIZE or len(team2) < TEAM_SIZE:
        await asyncio.sleep(1)

    await picks_msg.edit(content=None, embed=player_picks_embed, view=None)

    return team1, team2

''' ================================================== MAP/CATEGORY BANS ================================================== '''

class categoryButton(Button):
    def __init__(self, category_name):
        super().__init__(label=category_name, style=discord.ButtonStyle.red)
        self.category_name = category_name

    async def callback(self, interaction):
        global current_cap, team1_captain, team2_captain, categories, category_button_menu, category_embed

        if interaction.user == current_cap:
            if current_cap == team1_captain and len(categories) > 1:
                current_cap = team2_captain
            elif current_cap == team2_captain and len(categories) > 1:
                current_cap = team1_captain

            categories.remove(self.category_name)

            category_button_menu.remove_item(self)

            category_embed.clear_fields()
            for category in categories:
                category_embed.add_field(name=category, value='\n'.join(map_name for map_name in maps[category]), inline=True)
            category_embed.set_image(url="https://i.imgur.com/uo4ypUX.png")

            await interaction.message.edit(content=f"{current_cap.mention} please ban a category!", embed=category_embed, view=category_button_menu)
        else:
            await interaction.response.send_message("It is either not your turn, or you are not allowed to make a selection.", ephemeral=True)

class mapButton(Button):
    def __init__(self, map_name):
        super().__init__(label=map_name, style=discord.ButtonStyle.red)
        self.map_name = map_name

    async def callback(self, interaction):
        global current_cap, team1_captain, team2_captain, map_list, map_button_menu, map_embed

        if interaction.user == current_cap:
            if current_cap == team1_captain and len(map_list) > 1:
                current_cap = team2_captain
            elif current_cap == team2_captain and len(map_list) > 1:
                current_cap = team1_captain

            map_list.remove(self.map_name)

            map_button_menu.remove_item(self)

            map_embed.clear_fields()
            map_embed.add_field(name=categories[0], value='\n'.join(map_name for map_name in map_list), inline=True)
            map_embed.set_image(url="https://i.imgur.com/uo4ypUX.png")

            await interaction.message.edit(content=f"{current_cap.mention} please ban a map!", embed=map_embed, view=map_button_menu)
        else:
            await interaction.response.send_message("It is either not your turn, or you are not allowed to make a selection.", ephemeral=True)

async def start_map_ban(ctx, captain1, captain2, ban_channel, team1, team2):
    global current_cap, categories, game_ongoing, category_bool, map_list, category_button_menu, category_embed, map_button_menu, map_embed

    category_button_menu = View()
    for category in categories:
        category_button_menu.add_item(categoryButton(category))

    category_embed = discord.Embed(title="Category Veto", color=0x00ff00)
    for category in categories:
        category_embed.add_field(name=category, value='\n'.join(map_name for map_name in maps[category]), inline=True)
    category_embed.set_image(url="https://i.imgur.com/uo4ypUX.png")

    veto_msg = await ban_channel.send(content=f"{current_cap.mention}, please ban a category!", embed=category_embed, view=category_button_menu)
    while len(categories) > 1:
        if not game_ongoing:
            return
        await asyncio.sleep(1)

    map_list = list(maps.options(categories[0]))

    map_button_menu = View()
    for map_name in map_list:
        map_button_menu.add_item(mapButton(map_name))

    map_embed = discord.Embed(title="Map Veto", color=0x00ff00)
    map_embed.add_field(name=categories[0], value='\n'.join(map_name for map_name in map_list), inline=True)
    map_embed.set_image(url="https://i.imgur.com/uo4ypUX.png")

    await veto_msg.edit(content=f"{current_cap.mention}, please ban a map!", embed=map_embed, view=map_button_menu)
    while len(map_list) > 1:
        if not game_ongoing:
            return
        await asyncio.sleep(1)

    await veto_msg.edit(content=None, embed=map_embed, view=None)

    if game_ongoing:
        await ban_channel.send(f"The final map is: {map_list[0]}\n Reminder that one of the captains should /endgame after the game is over for the queue to reopen!")
        current_date_time = datetime.datetime.now().strftime("%B %d, %Y, %H:%M:%S")
        # Create the embed message
        embed = discord.Embed(title=f"Game: {current_date_time}", color=0x00ff00)
        embed.add_field(name="Map", value=map_list[0], inline=False)
        embed.add_field(name="Team 1", value='\n'.join([f'<@{user.id}>' for user in team1]), inline=True)
        embed.add_field(name="Team 2", value='\n'.join([f'<@{user.id}>' for user in team2]), inline=True)
        embed.set_footer(text=f"connect {SERVER_IP}:{SERVER_PORT}; password okkkkkkk")
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
    await change_map(SERVER_IP, SERVER_PORT, RCON_PASSWORD, map_list[0], map_ids)

async def change_map(server_ip, server_port, rcon_password, final_map, map_ids):
    # Connect to the Counter-Strike server using RCON
    try:
        with RCON((server_ip, int(server_port)), rcon_password) as rcon:
            # Notify players of the map change and set the new map
            rcon.execute('css_say Map changing...')
            rcon.execute(f'css_wsmap {map_ids[final_map]}')
            print("RCON commands executed successfully.")
    except Exception as e:
        print(f"Failed to execute RCON commands: {e}")

''' ================================================== TEST COMMANDS ================================================== ''' # remove after done
#Wingman mode for testing
@bot.tree.command(name="wingmanmode",description="Make it into wingman mode, (DO THIS BEFORE YOU OPENQUEUE)")
async def wingmanmode(ctx: discord.Interaction, enabled: bool):
    global TEAM_SIZE, PLAYER_COUNT
    if queue_open:
        await ctx.response.send_message(f"Queue must be closed to adjust mode", ephemeral=True)
    if enabled:
        TEAM_SIZE = 2
        PLAYER_COUNT = 4
        await ctx.response.send_message(f"Wingman mode has been enabled.", ephemeral=True)
    else:
        TEAM_SIZE = 5
        PLAYER_COUNT = 10
        await ctx.response.send_message(f"Wingman mode has been disabled.", ephemeral=True)
#changemap for testing
@bot.tree.command(name="changemap", description="test the rcon changemap")
async def changemap(ctx: discord.Interaction, map: str):
    global finalmap
    finalmap = map
    await change_map(SERVER_IP, SERVER_PORT, RCON_PASSWORD, finalmap, map_ids)
    await ctx.response.send_message(f"Changing map to {map}.", ephemeral=True)

#debug commands to add and remove players from queue
@bot.tree.command(name="addplayer", description="Manually add a player to the queue")
async def add_player(ctx: discord.Interaction, name: str):
    global queue
    user = discord.utils.get(ctx.guild.members, name=name)
    if user:
        if user not in queue:
            queue.append(user)
            await ctx.response.send_message(f"{user.name} has been added to the queue.", ephemeral=True)
        else:
            await ctx.response.send_message("This user is already in the queue.", ephemeral=True)
    else:
        await ctx.response.send_message("No user found with that name in this server.", ephemeral=True)

@bot.tree.command(name="removeplayer", description="Manually remove a player from the queue")
async def remove_player(ctx: discord.Interaction, name: str):
    global queue
    user = discord.utils.get(ctx.guild.members, name=name)
    if user:
        if user in queue:
            queue.remove(user)
            await ctx.response.send_message(f"{user.name} has been removed from the queue.", ephemeral=True)
        else:
            await ctx.response.send_message("This user is not in the queue.", ephemeral=True)
    else:
        await ctx.response.send_message("No user found with that name in this server.", ephemeral=True)

# Run the bot with your token
API_KEY = os.getenv("API_KEY")
bot.run(API_KEY)
