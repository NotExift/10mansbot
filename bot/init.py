import discord
from discord.ext import commands
import configparser
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

# Create a bot instance
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Global Variables
PLAYER_COUNT = 10
TEAM_SIZE = 5
SERVER_IP = os.getenv("SERVER_IP")
SERVER_PORT = os.getenv("SERVER_PORT")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

# Channel Variables
BAN_CHANNEL = None
PICK_CHANNEL = None
QUEUE_CHANNEL = None
GAME_CHANNEL = None
VOICE_CHANNEL = None

# SQL Variables
SQLHOST = os.getenv("SQLHOST")
SQLUSER = os.getenv("SQLUSER")
SQLPORT = os.getenv("SQLPORT")
SQLUSERPASSWORD = os.getenv("SQLUSERPASS")

# APIKEYS
STEAMAPIKEY = os.getenv("STEAMAPIKEY")
FACEITAPIKEY = os.getenv("FACEITAPIKEY")

# Queue Variables
QUEUE = []
QUEUE_MSG = None
QUEUE_OPEN = False
GAME_ONGOING = False
ACCEPT_TIME = 30
TEAM1_CAP = None
TEAM2_CAP = None
TEAM1 = None
TEAM2 = None

# Config Variables
MAX_CONFIG_FILES = int(
    os.getenv("MAX_CONFIG_FILES", "5")
)  # max amount of configs this instance of the bot can have at once
CONFIG_DIRECTORY = os.getenv("CONFIG_DIRECTORY", "./configs")
config_file = "configs/maps.cfg"  # default config file
MAPS = configparser.ConfigParser()
MAPS.read(config_file)
CATEGORIES = None
MAP_IDS = None
QUEUEPOP_MP3 = os.getenv(f"{CONFIG_DIRECTORY}/QUEUE_POP_AUDIO")


def format_username(username):
    return username.replace("_", "\_")


def set_map_config():
    global CATEGORIES, MAP_IDS
    CATEGORIES = list(MAPS.sections())
    MAP_IDS = {}
    for category in MAPS.sections():
        for map_name, map_id in MAPS.items(category):
            MAP_IDS[map_name] = map_id


# Event
@bot.event
async def on_ready():
    global BAN_CHANNEL, PICK_CHANNEL, QUEUE_CHANNEL, GAME_CHANNEL, VOICE_CHANNEL
    BAN_CHANNEL = bot.get_channel(int(os.getenv("BAN_CHANNEL")))
    PICK_CHANNEL = bot.get_channel(int(os.getenv("PICK_CHANNEL")))
    QUEUE_CHANNEL = bot.get_channel(int(os.getenv("QUEUE_CHANNEL")))
    GAME_CHANNEL = bot.get_channel(int(os.getenv("GAMELOG_CHANNEL")))
    VOICE_CHANNEL = bot.get_channel(int(os.getenv("VOICE_CHANNEL")))
    print(f"Bot is ready and logged in as {bot.user}!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
