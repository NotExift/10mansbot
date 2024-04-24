import mysql.connector
import re
import requests
from init import SQLHOST, SQLUSERPASSWORD, SQLPORT, SQLUSER
from mysql.connector import Error

database = "steamlink"
try:
    connection = mysql.connector.connect(
        host=SQLHOST,
        user=SQLUSER,
        passwd=SQLUSERPASSWORD,
        port=SQLPORT,
        database=database,
    )
    print("MySQL Database connection successful")
except Error as e:
    print(f"The error '{e}' occurred")


cursor = connection.cursor()


# Create the 'steamlink' database if it does not exist
create_database_query = "CREATE DATABASE IF NOT EXISTS steamlink"

# SQL query for creating the table, only if it does not exist
create_userinfo_table = """
    CREATE TABLE userinfo (
        id INT AUTO_INCREMENT PRIMARY KEY,
        discorduserid VARCHAR(255) NOT NULL,
        discordusername VARCHAR(255) NOT NULL,
        steamid VARCHAR(255) NOT NULL,
        faceitelo INT NOT NULL,
        faceitrank INT NOT NULL
    );
    """


def extract_steam64id(input_string, api_key):
    # Check if the input is already a Steam64 ID
    if input_string.isdigit() and len(input_string) == 17:
        return input_string

    # Prepare to extract or resolve Steam64 ID from URL
    steam_profile_pattern = r"https?://steamcommunity\.com/(profiles|id)/([a-zA-Z0-9]+)"
    match = re.match(steam_profile_pattern, input_string)
    if match:
        type_url, identifier = match.groups()

        # If the URL is directly to a numeric ID under profiles
        if type_url == "profiles" and identifier.isdigit():
            return identifier

        # If the URL is a custom ID, use the Steam API to resolve it
        if type_url == "id":
            api_url = f"http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={api_key}&vanityurl={identifier}"
            response = requests.get(api_url)
            data = response.json()
            if data["response"]["success"] == 1:
                return data["response"]["steamid"]
    # Return None if nothing is resolved
    return None


def get_faceit(steamid, api_key):
    url = "https://open.faceit.com/data/v4/players"
    params = {"game": "cs2", "game_player_id": steamid}
    headers = {"accept": "application/json", "Authorization": f"Bearer {api_key}"}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    faceit_elo = data.get("games", {}).get("cs2", {}).get("faceit_elo")
    faceit_rank = data.get("games", {}).get("cs2", {}).get("skill_level")

    return faceit_elo, faceit_rank
