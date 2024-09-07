# Discord Server Cloner

This is a powerful and customizable Discord Server Cloning tool built using `discord.py` version 1.6.0. It allows you to copy entire servers, save their data to JSON, load servers from JSON, wipe servers, and more. This tool is useful for server management, replication, and backups.

## Table of Contents
1. [Features](#features)
2. [Requirements](#requirements)
3. [Setup](#setup)
4. [Usage](#usage)
5. [Commands Overview](#commands-overview)
6. [Logging](#logging)
7. [Known Issues and Troubleshooting](#known-issues-and-troubleshooting)
8. [License](#license)

---

## Features

- **Live Copy**: Clone a server's roles, channels, and emojis in real-time to another server.
- **Server Save**: Save all server information, including roles, channels, and permissions, to a JSON file.
- **Server Load**: Load server data from a JSON file and replicate the entire server structure into a new server.
- **Multi-Server Cloning**: Clone multiple servers simultaneously.
- **Server Wipe**: Remove all roles, channels, and emojis from a server while preserving its members.
- **Customizable**: Supports configuration of various features like server icons, role permissions, and more.

---

## Requirements

- Python 3.6 or higher
- `discord.py` 1.6.0
- `aiohttp`
- `tqdm` for progress bars
- Optional: `logging` for detailed activity tracking

---

## Setup

### 1. Clone the repository
```bash
https://github.com/YaBoiSwayZ/Discord-Guild-Cloner.git
cd discord-server-cloner
```

### 2. Install dependencies
```bash
pip install discord.py aiohttp tqdm
```

### 3. Add your Discord Token
Replace `TOKEN` in the script with your Discord user token:
```python
TOKEN = 'YOUR_DISCORD_TOKEN'
```

⚠️ **Important**: This script uses a user token (not a bot token), which means it logs in as your account. Be sure to follow Discord's [Terms of Service](https://discord.com/terms) and note that misuse of user tokens may lead to account suspension.

---

## Usage

1. Run the script:
   ```bash
   python cloner.py
   ```

2. After logging in, you will be presented with a menu where you can select different actions:

```bash
==========================================
       DISCORD SERVER CLONER
==========================================
Options:
1. Live Copy (Copy server to another server)
2. Server Save (Save server data to a JSON file)
3. Server Load (Load server data from JSON file)
4. Multi-Server Cloning (Clone multiple servers at once)
5. Server Wipe (Wipe a server clean except for members)
6. Exit
==========================================
```

3. Follow the on-screen prompts to provide the necessary server IDs and execute the selected action.

---

## Commands Overview

### 1. **Live Copy**
- Clones a source server to a target server, including roles, channels, and emojis.
- Input required: Source Guild ID, Target Guild ID.

### 2. **Server Save**
- Saves the server configuration (roles, channels, permissions, etc.) to a JSON file for future use.
- Input required: Source Guild ID.

### 3. **Server Load**
- Loads a saved JSON configuration and replicates the server structure into a new server.
- Input required: JSON file, Target Guild ID.

### 4. **Multi-Server Cloning**
- Allows the user to clone multiple servers at once by specifying comma-separated lists of source and target guild IDs.
- Input required: Source Guild IDs, Target Guild IDs.

### 5. **Server Wipe**
- Wipes the server by deleting all roles, channels, and emojis while keeping the members intact.
- Input required: Target Guild ID.

---

## Logging

All actions performed by the script are logged into a file named `server_clone.log`. This log file is useful for troubleshooting or reviewing actions. 

Sample log entry:
```
2024-09-07 12:35:22 - INFO - Logged in as YourDiscordUserName#1234
2024-09-07 12:37:45 - INFO - Cloning server 'SourceServer' to 'TargetServer'
2024-09-07 12:40:10 - ERROR - Failed to clone emoji 'ExampleEmoji': Missing Permissions
```

---

## Known Issues and Troubleshooting

1. **Missing Permissions**:
   - Ensure the account used has the required permissions in both the source and target servers (Manage Roles, Manage Channels, Manage Emojis, etc.).

2. **Server Wipe Icon Retrieval Fails**:
   - If the server wipe process fails to fetch the custom icon (`ICON_URL`), the server will default to no icon. Check the `server_clone.log` for detailed error messages.

3. **Role/Permission Mapping Errors**:
   - During server load, if certain role IDs from the JSON file do not exist in the target server, permission mappings for those roles will be skipped. A log message will indicate the missing role IDs.

---

## License

This project is licensed under the MIT License. Feel free to modify and distribute as needed.
