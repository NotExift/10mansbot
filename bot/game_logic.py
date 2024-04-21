import discord
from discord.ui import Button, View
from valve.rcon import RCON
import random
import asyncio
import datetime
from init import *

async def display_queue(ctx):
    global QUEUE_MSG, GAME_ONGOING, TEAM1_CAP, TEAM2_CAP, TEAM1, TEAM2
    previous_queue = []
    QUEUE_MSG = await QUEUE_CHANNEL.send(embed=discord.Embed(title="Queue now open", color=0x00ff00))
    while True:
        if not QUEUE_OPEN:
            embed = discord.Embed(title="Queue is currently closed.", color=0x00ff00)
            if QUEUE_MSG:
                await QUEUE_MSG.delete()
            QUEUE_MSG = await QUEUE_CHANNEL.send(embed=embed)
            return  # Exit the function if queue is closed

        # Update queue display if it has changed
        curr_player_count = len(QUEUE)
        if curr_player_count != len(previous_queue):
            queue_display = '\n'.join([format_username(user.name) for user in QUEUE])
            embed = discord.Embed(title="Current Queue", description=queue_display, color=0x00ff00)
            embed.set_footer(text=f"Player count: {curr_player_count}/{str(PLAYER_COUNT)}")
            if QUEUE_MSG:
                await QUEUE_MSG.delete()
            QUEUE_MSG = await QUEUE_CHANNEL.send(embed=embed)
            previous_queue = list(QUEUE)

        if curr_player_count == PLAYER_COUNT and not GAME_ONGOING:
            GAME_ONGOING = True
            TEAM1_CAP, TEAM2_CAP = random.sample(QUEUE, 2)  # Select two random captains
            captain_role = discord.utils.get(ctx.guild.roles, name="captain")
            await TEAM1_CAP.add_roles(captain_role)
            await TEAM2_CAP.add_roles(captain_role)
            TEAM1, TEAM2 = await pick_players()  # Captains pick players in pick_channel
            embed = discord.Embed(title="Game Ongoing", color=0x00ff00)
            embed.add_field(name="Team 1", value='\n'.join([user.name for user in TEAM1]), inline=True)
            embed.add_field(name="Team 2", value='\n'.join([user.name for user in TEAM2]), inline=True)
            embed.set_footer(text=f"Captains: {TEAM1_CAP.name}, {TEAM2_CAP.name}")
            if QUEUE_MSG:  # If there is a previous message, delete it
                await QUEUE_MSG.delete()
            QUEUE_MSG = await QUEUE_CHANNEL.send(embed=embed)
            try:
                await start_map_ban(ctx)  # Assuming start_map_ban uses the channel for communication
            except Exception as e:
                print(f"Error in start_map_ban: {e}")
        await asyncio.sleep(3)

''' ================================================== PLAYER PICK ================================================== '''

class playerButton(Button):
    def __init__(self, player):
        super().__init__(label=player.name, style=discord.ButtonStyle.green)
        self.player = player
    
    async def callback(self, interaction):
        global TEAM1, TEAM2, current_cap, player_button_menu, player_picks_embed

        if interaction.user == current_cap:
            if current_cap == TEAM1_CAP and len(TEAM1) < TEAM_SIZE:
                TEAM1.append(self.player)
                current_cap = TEAM2_CAP
            elif current_cap == TEAM2_CAP and len(TEAM2) < TEAM_SIZE:
                TEAM2.append(self.player)
                current_cap = TEAM1_CAP

            # Remove this button from the view
            player_button_menu.remove_item(self)

            player_picks_embed = player_picks_embed(player_picks_embed)
            player_picks_embed.clear_fields()
            player_picks_embed.add_field(name="Team 1", value='\n'.join([f'<@{user.id}>' for user in TEAM1]), inline=True)
            player_picks_embed.add_field(name="Team 2", value='\n'.join([f'<@{user.id}>' for user in TEAM2]), inline=True)

            await interaction.message.edit(content=f"{current_cap.mention} please select a player!", embed=player_picks_embed, view=player_button_menu)
        else:
            await interaction.response.send_message("It is either not your turn, or you are not allowed to make a selection.", ephemeral=True)

async def pick_players():
    global TEAM1, TEAM2, current_cap, player_button_menu, player_picks_embed
    TEAM1 = [TEAM1_CAP]
    TEAM2 = [TEAM2_CAP]
    current_cap = TEAM1_CAP

    player_button_menu = View()
    for player in QUEUE:
        if player != TEAM1_CAP and player != TEAM2_CAP:
            player_button_menu.add_item(playerButton(player))

    player_picks_embed = discord.Embed(title="Player Picks", color=0x00ff00)
    player_picks_embed.add_field(name="Team 1", value='\n'.join([f'<@{user.id}>' for user in TEAM1]), inline=True)
    player_picks_embed.add_field(name="Team 2", value='\n'.join([f'<@{user.id}>' for user in TEAM2]), inline=True)

    picks_msg = await QUEUE_CHANNEL.send(content=f"{current_cap.mention} please select a player!", embed=player_picks_embed, view=player_button_menu)

    while len(TEAM1) < TEAM_SIZE or len(TEAM2) < TEAM_SIZE:
        await asyncio.sleep(1)

    await picks_msg.edit(content=None, embed=player_picks_embed, view=None)

    return TEAM1, TEAM2

''' ================================================== MAP/CATEGORY BANS ================================================== '''

class categoryButton(Button):
    def __init__(self, category_name):
        super().__init__(label=category_name, style=discord.ButtonStyle.red)
        self.category_name = category_name

    async def callback(self, interaction):
        global CATEGORIES, current_cap, category_button_menu, category_embed

        if interaction.user == current_cap:
            if current_cap == TEAM1_CAP and len(CATEGORIES) > 1:
                current_cap = TEAM2_CAP
            elif current_cap == TEAM2_CAP and len(CATEGORIES) > 1:
                current_cap = TEAM1_CAP

            CATEGORIES.remove(self.category_name)

            category_button_menu.remove_item(self)

            category_embed.clear_fields()
            for category in CATEGORIES:
                category_embed.add_field(name=category, value='\n'.join(map_name for map_name in MAPS[category]), inline=True)
            category_embed.set_image(url="https://i.imgur.com/uo4ypUX.png")

            await interaction.message.edit(content=f"{current_cap.mention} please ban a category!", embed=category_embed, view=category_button_menu)
        else:
            await interaction.response.send_message("It is either not your turn, or you are not allowed to make a selection.", ephemeral=True)

class mapButton(Button):
    def __init__(self, map_name):
        super().__init__(label=map_name, style=discord.ButtonStyle.red)
        self.map_name = map_name

    async def callback(self, interaction):
        global current_cap, map_list, map_button_menu, map_embed

        if interaction.user == current_cap:
            if current_cap == TEAM1_CAP and len(map_list) > 1:
                current_cap = TEAM2_CAP
            elif current_cap == TEAM2_CAP and len(map_list) > 1:
                current_cap = TEAM1_CAP

            map_list.remove(self.map_name)

            map_button_menu.remove_item(self)

            map_embed.clear_fields()
            map_embed.add_field(name=CATEGORIES[0], value='\n'.join(map_name for map_name in map_list), inline=True)
            map_embed.set_image(url="https://i.imgur.com/uo4ypUX.png")

            await interaction.message.edit(content=f"{current_cap.mention} please ban a map!", embed=map_embed, view=map_button_menu)
        else:
            await interaction.response.send_message("It is either not your turn, or you are not allowed to make a selection.", ephemeral=True)

async def start_map_ban(ctx):
    global current_cap, map_list, category_button_menu, category_embed, map_button_menu, map_embed

    set_map_config()

    category_button_menu = View()
    for category in CATEGORIES:
        category_button_menu.add_item(categoryButton(category))

    category_embed = discord.Embed(title="Category Veto", color=0x00ff00)
    for category in CATEGORIES:
        category_embed.add_field(name=category, value='\n'.join(map_name for map_name in MAPS[category]), inline=True)
    category_embed.set_image(url="https://i.imgur.com/uo4ypUX.png")

    veto_msg = await BAN_CHANNEL.send(content=f"{current_cap.mention}, please ban a category!", embed=category_embed, view=category_button_menu)
    while len(CATEGORIES) > 1:
        if not GAME_ONGOING:
            return
        await asyncio.sleep(1)

    map_list = list(MAPS.options(CATEGORIES[0]))

    map_button_menu = View()
    for map_name in map_list:
        map_button_menu.add_item(mapButton(map_name))

    map_embed = discord.Embed(title="Map Veto", color=0x00ff00)
    map_embed.add_field(name=CATEGORIES[0], value='\n'.join(map_name for map_name in map_list), inline=True)
    map_embed.set_image(url="https://i.imgur.com/uo4ypUX.png")

    await veto_msg.edit(content=f"{current_cap.mention}, please ban a map!", embed=map_embed, view=map_button_menu)
    while len(map_list) > 1:
        if not GAME_ONGOING:
            return
        await asyncio.sleep(1)

    await veto_msg.edit(content=None, embed=map_embed, view=None)

    if GAME_ONGOING:
        await BAN_CHANNEL.send(f"The final map is: {map_list[0]}\n Reminder that one of the captains should /endgame after the game is over for the queue to reopen!")
        current_date_time = datetime.datetime.now().strftime("%B %d, %Y, %H:%M:%S")
        button = Button(label="Click to Join Server", style=discord.ButtonStyle.url, url="http://connect.exift.gay/")
        view = View()
        view.add_item(button)
        # Create the embed message
        embed = discord.Embed(title=f"Game: {current_date_time}", color=0x00ff00)
        embed.add_field(name="Map", value=map_list[0], inline=False)
        embed.add_field(name="Team 1", value='\n'.join([f'<@{user.id}>' for user in TEAM1]), inline=True)
        embed.add_field(name="Team 2", value='\n'.join([f'<@{user.id}>' for user in TEAM2]), inline=True)
        embed.set_footer(text=f"connect {SERVER_IP}:{SERVER_PORT}; password okkkkkkk")
        # Send the embed message to the game channel
        await GAME_CHANNEL.send(embed=embed, view=view)
        # Create a new embed message for the players
        player_embed = discord.Embed(title="Your game is ready! The server may take a minute before switching maps, please be patient.", color=0x00ff00)
        player_embed.add_field(name="Map", value=map_list[0], inline=False)
        player_embed.add_field(name="Team 1", value='\n'.join([f'<@{user.id}>' for user in TEAM1]), inline=True)
        player_embed.add_field(name="Team 2", value='\n'.join([f'<@{user.id}>' for user in TEAM2]), inline=True)
        player_embed.set_footer(text=f"connect {SERVER_IP}:{SERVER_PORT}; password okkkkkkk")
        # Get the role object for "Match Notifications"
        match_notifications_role = discord.utils.get(ctx.guild.roles, name="Match Notifications")
        # Filter the players who have the "Match Notifications" role
        players_with_role = [player for player in TEAM1 + TEAM2 if match_notifications_role in player.roles]
        # Send the embed message to each player with the "Match Notifications" role
        for player in players_with_role:
            try:
                await player.send(embed=player_embed, view=view)
            except Exception as e:
                print(f"Couldn't send message to {player.name}: {e}")
        # Create a valve rcon connection to the counterstrike server
    await change_map(map_list[0])

async def change_map(final_map):
    # Connect to the Counter-Strike server using RCON
    try:
        with RCON((SERVER_IP, int(SERVER_PORT)), RCON_PASSWORD) as rcon:
            # Notify players of the map change and set the new map
            rcon.execute('css_say Map changing...')
            rcon.execute(f'css_wsmap {MAP_IDS[final_map]}')
            print("RCON commands executed successfully.")
    except Exception as e:
        print(f"Failed to execute RCON commands: {e}")