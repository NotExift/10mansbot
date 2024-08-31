# CS2 Workshop Map Queue Bot
A Discord bot designed to queue 10 players into CS2 workshop map games, with automated team selection, map vetoes, and server management. This bot is optimized for a seamless experience in organizing and managing custom games.

## Features
- **Queue System**: Users can join the queue by clicking a button in the designated channel.
- **Unqueue Option**: Users can unqueue at any time before the match pops.
- **Automated Match Creation**: Once 10 players have joined the queue, a private text channel is created for match preparation.
- **Ready Check**: Players have 30 seconds to click the ready button. If not all players are ready, those who didn't respond are removed, and the channel is deleted.
- **Team Selection**: Two captains are randomly selected to pick their teams in an alternating fashion.
- **Map Veto**: Captains veto map categories first, followed by individual maps, until one map remains.
- **Server Management**: The server is automatically booted up with the selected map, and the IP address is shared with the players.
- **End Match**: Admins or team captains can end the match, which shuts down the server, deletes the channel, and logs the game information.

## Setup

### Prerequisites
- Python
- Pycord
- CS2 Dedicated Server

### Installation
*Still under construction*
1. Clone this repository. ```git clone https://github.com/NotExift/10mansbot.git```
2. Install dependencies. ```npm install```

### Configuration
1. Configure environment variables.
    - Create ```.env``` file.
    - `SERVER_IP` = Your server IP
    - `SERVER_PORT` = Your server port
    - `RCON_PASSWORD` = Your server password
    - `QUEUE_CHANNEL` = Your Discord server's `#queue` channel
    - `GAMELOG_CHANNEL` = Your Discord server's `#games-log` channel
    - `VOICE_CHANNEL` = Your Discord server's primary voice channel
    - `API_KEY` = Your Discord bot token.
    - *Many more I'm sure*
2. Start the bot. `python bot/main.py`

## Commands

### User Commands
| Command Name | Description |
| ------------ | ------------ |
| `/mappool` | List the current loaded mappool |

### Admin Commands
| Command Name | Description |
| ------------ | ------------ |
| `/openqueue` | Creates the initial queue instance so users can join |
| `/closequeue` | Closes the queue instance |
| `/wingmanmode` | Toggles wingman mode (2v2) |
| `/changemap` | Test the RCON changemap |
| `/addplayer` | Manually add a player to the queue |
| `/removeplayer` | Manually remove a player from the queue |
| `/forcereadyall` | Manually ready all players when the match pops |
| `/setcaptains` | Manually set captains |
| `/clearcaptains` | Clear out manually set captains |
| `/loadconfig` | Select and load a map's config file |
| `/add_category` | Add a new category to the configuration |
| `/add_map` | Add or update a map in a category |
| `/remove_category` | Remove a category from the configuration |
| `/remove_map` | Remove a map from a category |
| `/showconfig` | List the current loaded config |
| `/regeneratemapimage` | Regenerate the image for the map pool |

## Bot Workflow
1. **Queueing**: Users click the queue button to join. The bot tracks the number of users in the queue.
2. **Match Creation**: When 10 users are queued, the bot creates a private text channel for the match.
3. **Ready Check**: Players must click the ready button within 60 seconds. If not, they are removed from the queue, and the match is canceled.
4. **Team Selection**: Two captains are selected, and they alternate picking players by clicking buttons. If the captains do not make a selection in 20 seconds, a random player will be assigned to their team.
5. **Map Veto**: Captains veto categories and maps until one map remains. Again, if the captains do not make a selection in 20 seconds a random category/map will be selected to be removed.
6. **Server Launch**: The bot starts the server with the chosen map and sends the IP to the private text channel.
7. **Match End**: After the game, an admin or captain ends the match, in which the bot will shut down the server and log the results in the games-log channel.

## Visual Guide
*Insert image workflow here*

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
