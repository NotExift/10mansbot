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
1. Clone this repository. ```git clone https://github.com/NotExift/10mansbot.git```
2. Install dependencies. ```npm install```
3. Configure environment variables.
    - Create ```.env``` file.
    - `SERVER_IP` = 
    - `SERVER_PORT` = 
    - `RCON_PASSWORD` = 
    - `BAN_CHANNEL` = 
    - `PICK_CHANNEL` = 
    - `QUEUE_CHANNEL` = 
    - `GAMELOG_CHANNEL` = 
    - `VOICE_CHANNEL` = 
    - `API_KEY` = 