import mysql.connector
import re
import requests
from mysql.connector import Error

from init import SQLHOST, SQLUSERPASSWORD, SQLPORT, SQLUSER

def ensure_database_exists():
    try:
        # First, connect to MySQL server without specifying a database
        connection = mysql.connector.connect(
            host=SQLHOST,
            user=SQLUSER,
            passwd=SQLUSERPASSWORD,
            port=SQLPORT
        )
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS steamlink")
        cursor.close()
        connection.close()
        print("Database checked/created successfully.")
    except Error as e:
        print(f"An error occurred: {e}")
        return None

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=SQLHOST,
            user=SQLUSER,
            passwd=SQLUSERPASSWORD,
            port=SQLPORT,
            database="steamlink"
        )
        print("MySQL Database connection successful")
        return connection
    except Error as e:
        print(f"Failed to connect to the database: {e}")
        return None

# Call to ensure the database exists
ensure_database_exists()

# Now attempt to connect to the database
connection = connect_to_database()

if connection:
    cursor = connection.cursor()
    # Create the 'userinfo' table if it does not exist
    create_userinfo_table = """
        CREATE TABLE IF NOT EXISTS userinfo (
            id INT AUTO_INCREMENT PRIMARY KEY,
            discorduserid VARCHAR(255) NOT NULL,
            discordusername VARCHAR(255) NOT NULL,
            steamid VARCHAR(255) NOT NULL,
            faceitelo INT NOT NULL,
            faceitrank INT NOT NULL
        );
    """
    cursor.execute(create_userinfo_table)
    cursor.close()
    connection.close()
else:
    print("Connection to database was not established.")

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

def slink(user, userid):
    # Check if user already has an entry in the database
    check_query = "SELECT steamid FROM userinfo WHERE discorduserid = %s"
    cursor.execute(check_query, (userid,))
    result = cursor.fetchone()
    # Extract steamid using the given link
    steamid = extract_steam64id(link, STEAMAPIKEY)
    if not steamid:
        ctx.response.send_message("Invalid Steam link provided.")
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
            ctx.response.send_message(
                "Your Steam account has been updated successfully!", ephemeral=True
            )
        except Exception as e:
            ctx.response.send_message(
                f"Database update error: {str(e)}", ephemeral=True
            )
    else:
        # Insert new entry if no existing entry found
        insert_query = "INSERT INTO userinfo (discorduserid, discordusername, steamid, faceitelo, faceitrank) VALUES (%s, %s, %s, %s, %s)"
        data = (userid, user, steamid, elo, rank)
        try:
            cursor.execute(insert_query, data)
            connection.commit()
            ctx.response.send_message(
                "Steam Account Linked Successfully!", ephemeral=True
            )
        except Exception as e:
            ctx.response.send_message(
                f"Database upload error: {str(e)}", ephemeral=True
            )
