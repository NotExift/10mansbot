import discord
from discord.ui import Button, View
from valve.rcon import RCON
import random
import asyncio
import datetime
import init


async def start_match(ctx):
    init.GAME_ONGOING = True
    if (
        init.TEAM1_CAP is None or init.TEAM2_CAP is None
    ):  # check if captains has been set manually
        init.TEAM1_CAP, init.TEAM2_CAP = random.sample(
            init.QUEUE, 2
        )  # Select two random captains
    init.TEAM1, init.TEAM2 = (
        await pick_players()
    )  # Captains pick players in pick_channel
    embed = discord.Embed(title="Game Ongoing", color=0x00FF00)
    embed.add_field(
        name="👥 Team 1",
        value="\n".join([user.name for user in init.TEAM1]),
        inline=True,
    )
    embed.add_field(
        name="👥 Team 2",
        value="\n".join([user.name for user in init.TEAM2]),
        inline=True,
    )
    embed.set_footer(text=f"🧢 Captains: {init.TEAM1_CAP.name}, {init.TEAM2_CAP.name}")
    if init.QUEUE_MSG:  # If there is a previous message, delete it
        await init.QUEUE_MSG.delete()
    init.QUEUE_MSG = await init.QUEUE_CHANNEL.send(embed=embed)
    try:
        await start_map_ban(
            ctx
        )  # Assuming start_map_ban uses the channel for communication
    except Exception as e:
        print(f"Error in start_map_ban: {e}")


""" ================================================== PLAYER PICK ================================================== """


class playerButton(Button):
    def __init__(self, player):
        super().__init__(label=player.name, style=discord.ButtonStyle.green)
        self.player = player

    async def callback(self, interaction):
        global current_cap, player_buttons, player_button_menu, player_picks_embed
        await interaction.response.defer(ephemeral=True)

        if interaction.user == current_cap:
            if current_cap == init.TEAM1_CAP and len(init.TEAM1) < init.TEAM_SIZE:
                init.TEAM1.append(self.player)
                current_cap = init.TEAM2_CAP
            elif current_cap == init.TEAM2_CAP and len(init.TEAM2) < init.TEAM_SIZE:
                init.TEAM2.append(self.player)
                current_cap = init.TEAM1_CAP

            # Remove this button from the view
            player_buttons.remove(self)
            player_button_menu.remove_item(self)

            await interaction.followup.send(
                content=f"You have selected {self.player}!", ephemeral=True
            )
            await update_player_picks_message(interaction.message)
        else:
            await interaction.followup.send(
                "It is either not your turn, or you are not allowed to make a selection.",
                ephemeral=True,
            )


async def pick_players():
    global current_cap, player_buttons, player_button_menu, player_picks_embed
    init.TEAM1 = [init.TEAM1_CAP]
    init.TEAM2 = [init.TEAM2_CAP]
    current_cap = init.TEAM1_CAP

    player_button_menu = View()
    player_buttons = []
    for player in init.QUEUE:
        if player != init.TEAM1_CAP and player != init.TEAM2_CAP:
            button = playerButton(player)
            player_buttons.append(button)
            player_button_menu.add_item(button)

    player_picks_embed = discord.Embed(title="Player Picks", color=0x00FF00)
    player_picks_embed.add_field(
        name="👥 Team 1",
        value="\n".join([f"<@{user.id}>" for user in init.TEAM1]),
        inline=True,
    )
    player_picks_embed.add_field(
        name="👥 Team 2",
        value="\n".join([f"<@{user.id}>" for user in init.TEAM2]),
        inline=True,
    )

    picks_msg = await init.MATCHROOM_CHANNEL.send(
        content=f"{current_cap.mention} please select a player!",
        embed=player_picks_embed,
        view=player_button_menu,
    )

    while len(init.TEAM1) < init.TEAM_SIZE or len(init.TEAM2) < init.TEAM_SIZE - 1:
        try:
            await asyncio.wait_for(
                wait_for_captain_decision(current_cap), timeout=init.VETO_WINDOW
            )
        except asyncio.TimeoutError:
            # Timeout occurred, automatically ban a category
            button = (
                player_buttons.pop()
            )  # Remove last item, we can change this later if needed
            player_button_menu.remove_item(button)
            if current_cap == init.TEAM1_CAP:
                init.TEAM1.append(button.player)
                current_cap = init.TEAM2_CAP
            else:
                init.TEAM2.append(button.player)
                current_cap = init.TEAM1_CAP
            await update_player_picks_message(picks_msg)

    init.TEAM2.append(player_buttons[0].player)
    await update_player_picks_message(picks_msg)

    await picks_msg.edit(content=None, embed=player_picks_embed, view=None)

    return init.TEAM1, init.TEAM2


async def update_player_picks_message(message):
    global player_button_menu, player_picks_embed
    player_picks_embed.clear_fields()
    player_picks_embed.add_field(
        name="👥 Team 1",
        value="\n".join([f"<@{user.id}>" for user in init.TEAM1]),
        inline=True,
    )
    player_picks_embed.add_field(
        name="👥 Team 2",
        value="\n".join([f"<@{user.id}>" for user in init.TEAM2]),
        inline=True,
    )

    await message.edit(
        content=f"{current_cap.mention} please select a player!",
        embed=player_picks_embed,
        view=player_button_menu,
    )


""" ================================================== MAP/CATEGORY BANS ================================================== """


class categoryButton(Button):
    def __init__(self, category_name):
        super().__init__(label=category_name, style=discord.ButtonStyle.red)
        self.category_name = category_name

    async def callback(self, interaction):
        global current_cap, category_buttons, category_button_menu, category_embed
        await interaction.response.defer(ephemeral=True)

        if interaction.user == current_cap:
            if current_cap == init.TEAM1_CAP and len(init.CATEGORIES) > 1:
                current_cap = init.TEAM2_CAP
            elif current_cap == init.TEAM2_CAP and len(init.CATEGORIES) > 1:
                current_cap = init.TEAM1_CAP

            init.CATEGORIES.remove(self.category_name)
            category_buttons.remove(self)
            category_button_menu.remove_item(self)

            await interaction.followup.send(
                content=f"You have removed {self.category_name}!", ephemeral=True
            )
            await update_category_veto_message(interaction.message)
        else:
            await interaction.followup.send(
                "It is either not your turn, or you are not allowed to make a selection.",
                ephemeral=True,
            )


class mapButton(Button):
    def __init__(self, map_name):
        super().__init__(label=map_name, style=discord.ButtonStyle.red)
        self.map_name = map_name

    async def callback(self, interaction):
        global current_cap, map_list, map_buttons, map_button_menu, map_embed
        await interaction.response.defer(ephemeral=True)

        if interaction.user == current_cap:
            if current_cap == init.TEAM1_CAP and len(map_list) > 1:
                current_cap = init.TEAM2_CAP
            elif current_cap == init.TEAM2_CAP and len(map_list) > 1:
                current_cap = init.TEAM1_CAP

            map_list.remove(self.map_name)
            map_buttons.remove(self)
            map_button_menu.remove_item(self)

            await interaction.followup.send(
                content=f"You have removed {self.map_name}!", ephemeral=True
            )
            await update_map_veto_message(interaction.message)
        else:
            await interaction.followup.send(
                "It is either not your turn, or you are not allowed to make a selection.",
                ephemeral=True,
            )


class copyIPButton(Button):
    def __init__(self):
        super().__init__(label="Copy: connect IP", style=discord.ButtonStyle.gray)

    async def callback(self, interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user in init.TEAM1 or interaction.user in init.TEAM2:
            await interaction.followup.send(
                f"connect {init.SERVER_IP}:{init.SERVER_PORT}; password okkkkkkk",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "You are not in this match.", ephemeral=True
            )


class endgameButton(Button):
    def __init__(self):
        super().__init__(label="End Game", style=discord.ButtonStyle.red)

    async def callback(self, interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user in [init.TEAM1_CAP, init.TEAM2_CAP] or "Admin" in [
            role.name for role in interaction.user.roles
        ]:
            init.GAME_ONGOING = False
            init.QUEUE.clear()
            init.TEAM1.clear()
            init.TEAM2.clear()
            await interaction.followup.send("The game has ended.", ephemeral=True)
            try:
                await interaction.channel.delete()
                print(f"Channel matchroom-{init.MATCH_ID} was deleted successfully!")
            except Exception as e:
                print(
                    f"An error occurred: {e}\nChannel matchroom-{init.MATCH_ID} failed to be deleted!"
                )
        else:
            await interaction.followup.send(
                "You do not have the permissions to end the game.", ephemeral=True
            )


async def start_map_ban(ctx):
    global current_cap, map_list, category_buttons, map_buttons, category_button_menu, category_embed, map_button_menu, map_embed

    init.set_map_config()  # every time a new game is started the list resets

    category_button_menu = View()
    category_buttons = []
    for category in init.CATEGORIES:
        button = categoryButton(category)
        category_buttons.append(button)
        category_button_menu.add_item(button)

    category_embed = discord.Embed(title="Category Veto", color=0x00FF00)
    for category in init.CATEGORIES:
        category_embed.add_field(
            name=category,
            value="\n".join(map_name for map_name in init.MAPS[category]),
            inline=True,
        )
    category_embed.set_image(url="attachment://mapsimage.jpg")

    veto_msg = await init.MATCHROOM_CHANNEL.send(
        content=f"{current_cap.mention}, please ban a category!",
        file=discord.File(f"bot/mapsimage.jpg", filename=f"mapsimage.jpg"),
        embed=category_embed,
        view=category_button_menu,
    )

    while len(init.CATEGORIES) > 1:
        if not init.GAME_ONGOING:
            return
        # Wait for captain to make a decision within 20 seconds
        try:
            await asyncio.wait_for(
                wait_for_captain_decision(current_cap), timeout=init.VETO_WINDOW
            )
        except asyncio.TimeoutError:
            # Timeout occurred, automatically ban a category
            init.CATEGORIES.pop()  # Remove last item, we can change this later if needed
            button = category_buttons.pop()
            category_button_menu.remove_item(button)
            if current_cap == init.TEAM1_CAP:
                current_cap = init.TEAM2_CAP
            else:
                current_cap = init.TEAM1_CAP
            await update_category_veto_message(veto_msg)

    map_list = list(init.MAPS.options(init.CATEGORIES[0]))

    map_button_menu = View()
    map_buttons = []
    for map_name in map_list:
        button = mapButton(map_name)
        map_buttons.append(button)
        map_button_menu.add_item(button)

    map_embed = discord.Embed(title="Map Veto", color=0x00FF00)
    map_embed.add_field(
        name=init.CATEGORIES[0],
        value="\n".join(map_name for map_name in map_list),
        inline=True,
    )
    await veto_msg.edit(
        content=f"{current_cap.mention}, please ban a map!",
        embed=map_embed,
        view=map_button_menu,
    )

    while len(map_list) > 1:
        if not init.GAME_ONGOING:
            return
        # Wait for captain to make a decision within 20 seconds
        try:
            await asyncio.wait_for(
                wait_for_captain_decision(current_cap), timeout=init.VETO_WINDOW
            )
        except asyncio.TimeoutError:
            # Timeout occurred, automatically ban a category
            map_list.pop()  # Remove last item, we can change this later if needed
            button = map_buttons.pop()
            map_button_menu.remove_item(button)
            if current_cap == init.TEAM1_CAP:
                current_cap = init.TEAM2_CAP
            else:
                current_cap = init.TEAM1_CAP
            await update_map_veto_message(veto_msg)

    await veto_msg.edit(content=None, embed=map_embed, view=None)

    # Create a valve rcon connection to the counterstrike server
    await init.MATCHROOM_CHANNEL.send(
        "Please wait for your match server to to be created!"
    )
    await change_map(map_list[0])

    if init.GAME_ONGOING:
        current_date_time = datetime.datetime.now().strftime("%B %d, %Y, %H:%M:%S")
        server_button = Button(
            label="Click to Join Server",
            style=discord.ButtonStyle.url,
            url="http://connect.exift.gay/",
        )
        view = View(timeout=None)
        view.add_item(server_button)
        view.add_item(copyIPButton())
        view.add_item(endgameButton())
        # Create the embed message
        embed = discord.Embed(title=f"Game: {current_date_time}", color=0x00FF00)
        embed.add_field(name="Map", value=map_list[0], inline=False)
        embed.add_field(
            name="👥 Team 1",
            value="\n".join([f"<@{user.id}>" for user in init.TEAM1]),
            inline=True,
        )
        embed.add_field(
            name="👥 Team 2",
            value="\n".join([f"<@{user.id}>" for user in init.TEAM2]),
            inline=True,
        )
        imageid = init.MAP_IDS.get(map_list[0])
        try:
            embed.set_thumbnail(url=f"attachment://{imageid}.jpg")
        except:
            pass

        # Send the info message to the game_log channel
        ifile_game = discord.File(
            f"bot/thumbnail_cache/{imageid}.jpg", filename=f"{imageid}.jpg"
        )
        await init.GAME_CHANNEL.send(file=ifile_game, embed=embed)

        # Send the info message to the matchroom channel
        ifile_matchroom = discord.File(
            f"bot/thumbnail_cache/{imageid}.jpg", filename=f"{imageid}.jpg"
        )
        await init.MATCHROOM_CHANNEL.send(
            content=f'The final map is: **{map_list[0]}**\n Reminder that one of the captains need to click "endgame" whenever the match concludes to reopen the queue!',
            file=ifile_matchroom,
            embed=embed,
            view=view,
        )

        # Create a new embed message for the players
        player_view = View()
        player_view.add_item(server_button)
        player_view.add_item(copyIPButton())
        player_embed = discord.Embed(
            title="Your game is ready! The server may take a minute before switching maps, please be patient.",
            color=0x00FF00,
        )
        player_embed.add_field(name="Map", value=map_list[0], inline=False)
        player_embed.add_field(
            name="👥 Team 1",
            value="\n".join([f"<@{user.id}>" for user in init.TEAM1]),
            inline=True,
        )
        player_embed.add_field(
            name="👥 Team 2",
            value="\n".join([f"<@{user.id}>" for user in init.TEAM2]),
            inline=True,
        )
        try:
            player_embed.set_thumbnail(url=f"attachment://{imageid}.jpg")
        except:
            pass
        # Get the role object for "Match Notifications"
        match_notifications_role = discord.utils.get(
            ctx.guild.roles, name="Match Notifications"
        )
        # Filter the players who have the "Match Notifications" role
        players_with_role = [
            player
            for player in init.TEAM1 + init.TEAM2
            if match_notifications_role in player.roles
        ]
        # Send the embed message to each player with the "Match Notifications" role
        for player in players_with_role:
            ifile_player = discord.File(
                f"bot/thumbnail_cache/{imageid}.jpg", filename=f"{imageid}.jpg"
            )
            try:
                await player.send(
                    file=ifile_player, embed=player_embed, view=player_view
                )
            except Exception as e:
                print(f"Couldn't send message to {player.name}: {e}")


async def change_map(final_map):
    # Connect to the Counter-Strike server using RCON
    try:
        with RCON((init.SERVER_IP, int(init.SERVER_PORT)), init.RCON_PASSWORD) as rcon:
            # Notify players of the map change and set the new map
            rcon.execute("css_say Map changing...")
            rcon.execute(f"css_wsmap {init.MAP_IDS[final_map]}")
            print("RCON commands executed successfully.")
    except Exception as e:
        print(f"Failed to execute RCON commands: {e}")


async def wait_for_captain_decision(captain):
    while True:
        if current_cap != captain:
            # Captain is no longer who we were waiting for, meaning they have selected
            return
        await asyncio.sleep(1)


async def update_category_veto_message(message):
    global category_button_menu, category_embed

    category_embed.clear_fields()

    for category in init.CATEGORIES:
        category_embed.add_field(
            name=category,
            value="\n".join(map_name for map_name in init.MAPS[category]),
            inline=True,
        )
    category_embed.set_image(url="attachment://bot/mapsimage.jpg")

    await message.edit(
        content=f"{current_cap.mention} please ban a category!",
        embed=category_embed,
        view=category_button_menu,
    )


async def update_map_veto_message(message):
    global map_button_menu, map_embed

    map_embed.clear_fields()
    map_embed.add_field(
        name=init.CATEGORIES[0],
        value="\n".join(map_name for map_name in map_list),
        inline=True,
    )
    map_embed.set_image(url="attachment://bot/mapsimage.jpg")

    await message.edit(
        content=f"{current_cap.mention} please ban a map!",
        embed=map_embed,
        view=map_button_menu,
    )
