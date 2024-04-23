import os

from init import *
from user_commands import *
from admin_commands import *

# Run the bot with your token
API_KEY = os.getenv("API_KEY")
bot.run(API_KEY)