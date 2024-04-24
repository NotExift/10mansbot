import init
import discord
import os
from init import *
from discord.ext import commands
from discord.ui import Select, View


# Load specific config selection
def get_config_files():
    # List all files in the config directory up to the maximum number specified
    try:
        files = [f for f in os.listdir(CONFIG_DIRECTORY) if f.endswith(".cfg")]
        return files[: init.MAX_CONFIG_FILES]
    except FileNotFoundError:
        return []


class ConfigSelect(discord.ui.Select):
    def __init__(self, config_files):
        options = [
            discord.SelectOption(
                label=f"{filename}", description=f"Load {filename}", value=filename
            )
            for filename in config_files
        ]
        super().__init__(
            placeholder="Choose a configuration file...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        init.config_file = os.path.join(CONFIG_DIRECTORY, self.values[0])
        init.MAPS.clear()
        init.MAPS.read(init.config_file)
        await interaction.response.send_message(
            f"Loaded configuration from {init.config_file}!", ephemeral=True
        )


class ConfigSelectView(discord.ui.View):
    def __init__(self, config_files):
        super().__init__()
        self.add_item(ConfigSelect(config_files))
