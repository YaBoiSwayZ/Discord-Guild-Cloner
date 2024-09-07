import discord
import json
import asyncio
import logging
import os
import tqdm
import aiohttp
import re
from discord.ext import tasks

LOG_FILE = 'server_clone.log'
CLONED_DIR = "ClonedServers"
ICON_URL = "https://i.imgur.com/ld9MCIx.png"

logging.basicConfig(
    filename=LOG_FILE,
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

os.makedirs(CLONED_DIR, exist_ok=True)

def display_banner():
    print("""
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
    """)

async def progress_bar(task_count, description):
    bar = tqdm.tqdm(total=task_count, desc=description)
    for _ in range(task_count):
        bar.update(1)
        await asyncio.sleep(0)  # Allow other tasks to run
    bar.close()

class ServerCloner(discord.Client):
    async def on_ready(self):
        logging.info(f'Logged in as {self.user}')
        await self.main_menu()

    async def main_menu(self):
        while True:
            display_banner()
            choice = await self._get_user_input("Choose an option (1-6): ", ['1', '2', '3', '4', '5', '6'])
            if choice == '6':
                print("Exiting...")
                await self.close()  # Gracefully stop the bot
                break
            await self.route_action(choice)

    async def route_action(self, choice):
        try:
            actions = {
                '1': self.live_copy,
                '2': self.server_save,
                '3': self.server_load,
                '4': self.multi_server_clone,
                '5': self.server_wipe
            }
            await actions[choice]()
        except Exception as e:
            logging.error(f"Error: {e}")

    async def live_copy(self):
        src, tgt = await self._get_guild_ids("Live Copy")
        if src and tgt:
            await self._clone_guild(src, tgt)

    async def server_wipe(self):
        target_guild = await self._get_guild("Server Wipe", "Target Guild ID")
        if target_guild:
            await self._wipe_guild(target_guild)

    async def server_save(self):
        src_guild = await self._get_guild("Server Save", "Source Guild ID")
        if src_guild:
            await self._save_guild_data(src_guild)

    async def server_load(self):
        json_file = await self._choose_json_file()
        target_guild = await self._get_guild("Server Load", "Target Guild ID")
        if target_guild and json_file:
            await self._load_guild_data(json_file, target_guild)

    async def multi_server_clone(self):
        src_ids, tgt_ids = map(self._split_ids, await asyncio.gather(
            self._get_user_input("Multi-Server Clone - Source Guild IDs (comma-separated): "),
            self._get_user_input("Multi-Server Clone - Target Guild IDs (comma-separated): ")
        ))
        if len(src_ids) != len(tgt_ids):
            print("Source and Target IDs count mismatch.")
            return
        await asyncio.gather(*[self._clone_guild(src, tgt) for src, tgt in zip(src_ids, tgt_ids)])

    async def _clone_guild(self, src_guild, tgt_guild):
        logging.info(f"Cloning {src_guild.name} to {tgt_guild.name}")
        role_map = await self._clone_roles(src_guild, tgt_guild)
        await self._clone_channels(src_guild, tgt_guild, role_map)
        await self._clone_emojis(src_guild, tgt_guild)
        await self._set_guild_name_icon(src_guild, tgt_guild)
        logging.info(f"Cloning completed from {src_guild.name} to {tgt_guild.name}")

    async def _wipe_guild(self, guild):
        roles = [r for r in guild.roles if r.name != "@everyone"]
        channels = guild.channels
        await progress_bar(len(roles), "Deleting Roles")
        await self._delete_entities(roles, "role")
        await progress_bar(len(channels), "Deleting Channels")
        await self._delete_entities(channels, "channel")
        await self._wipe_emojis_stickers(guild)
        await self._reset_guild(guild)

    async def _save_guild_data(self, guild):
        sanitized_guild_name = re.sub(r'[<>:"/\\|?*]', '_', guild.name)
        json_file = os.path.join(CLONED_DIR, f"{sanitized_guild_name}_clone.json")
        
        server_data = await self._get_guild_data(guild)
        
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(server_data, f, ensure_ascii=False, indent=4)
            logging.info(f"Saved data to {json_file}")
            print(f"Server data saved to {json_file}")
        except Exception as e:
            logging.error(f"Error saving server data: {e}")

    async def _load_guild_data(self, json_file, guild):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        await self._load_data_to_guild(data, guild)

    async def _delete_entities(self, entities, entity_type):
        for entity in entities:
            try:
                await entity.delete(reason="Server wipe")
                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Failed to delete {entity_type} {entity.name}: {e}")

    async def _wipe_emojis_stickers(self, guild):
        entities = list(guild.emojis)
        try:
            stickers = await guild.stickers()
            entities.extend(stickers)
        except AttributeError:
            logging.warning("No stickers found.")
        await progress_bar(len(entities), "Deleting Emojis/Stickers")
        await self._delete_entities(entities, "emoji/sticker")

    async def _reset_guild(self, guild):
        try:
            blank_name = "\u1CBC\u1CBC"
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(ICON_URL) as resp:
                            if resp.status == 200:
                                icon_data = await resp.read()
                                await guild.edit(
                                    name=blank_name,
                                    icon=icon_data,
                                    verification_level=discord.VerificationLevel.none,
                                    default_notifications=discord.NotificationLevel.all_messages,
                                    explicit_content_filter=discord.ContentFilter.disabled,
                                    afk_channel=None,
                                    system_channel=None
                                )
                                logging.info(f"Server {guild.name} reset with new icon.")
                                print(f"Server {guild.name} wiped successfully and renamed to blank.")
                                break
                            else:
                                logging.error(f"Failed to retrieve server icon, status code: {resp.status}. Attempt {attempt+1} of {max_retries}.")
                except Exception as e:
                    logging.error(f"Error fetching server icon: {e}. Attempt {attempt+1} of {max_retries}.")
                await asyncio.sleep(2)  # Wait before retrying

            if attempt == max_retries - 1:
                logging.error("Failed to retrieve server icon after maximum retries.")
                await guild.edit(
                    name=blank_name,
                    icon=None,  # Fallback to no icon if it fails
                    verification_level=discord.VerificationLevel.none,
                    default_notifications=discord.NotificationLevel.all_messages,
                    explicit_content_filter=discord.ContentFilter.disabled,
                    afk_channel=None,
                    system_channel=None
                )
                logging.info(f"Server {guild.name} reset with no icon.")
                print(f"Server {guild.name} wiped successfully but icon retrieval failed.")
        except Exception as e:
            logging.error(f"Failed to reset server: {e}")

    async def _get_guild_ids(self, action_name):
        src = await self._get_guild(action_name, "Source Guild ID")
        tgt = await self._get_guild(action_name, "Target Guild ID")
        return src, tgt

    async def _get_guild(self, action_name, input_msg):
        try:
            guild_id = await self._get_user_input(f"{action_name} - {input_msg}: ")
            guild = self.get_guild(int(guild_id))
            if not guild:
                raise ValueError(f"Guild with ID {guild_id} not found.")
            return guild
        except ValueError as e:
            logging.error(f"Error fetching guild: {e}")
            return None

    async def _choose_json_file(self):
        files = sorted(os.listdir(CLONED_DIR))
        if not files:
            print("No saved servers found.")
            return None
        for i, file in enumerate(files):
            print(f"{i+1}. {file}")
        choice = await self._get_user_input("Choose file number: ")
        try:
            return os.path.join(CLONED_DIR, files[int(choice) - 1])
        except (ValueError, IndexError):
            print("Invalid choice.")
            return None

    async def _load_data_to_guild(self, data, guild):
        role_map = await self._load_roles(data['roles'], guild)
        await self._load_channels(data['channels']['categories'], guild, role_map)
        await self._set_guild_name_icon(data, guild)

    async def _get_user_input(self, prompt, valid_choices=None):
        while True:
            print(prompt)
            user_input = await asyncio.get_event_loop().run_in_executor(None, input)
            if valid_choices is None or user_input in valid_choices:
                return user_input
            else:
                print(f"Invalid input: {user_input}. Please try again.")

    async def _clone_roles(self, src_guild, tgt_guild):
        role_map = {}
        for role in sorted(src_guild.roles, key=lambda r: r.position, reverse=True):
            if role.name != "@everyone":
                try:
                    new_role = await tgt_guild.create_role(
                        name=role.name, permissions=role.permissions, colour=role.colour,
                        hoist=role.hoist, mentionable=role.mentionable
                    )
                    role_map[role.id] = new_role
                    await asyncio.sleep(1)
                except Exception as e:
                    logging.error(f"Error cloning role {role.name}: {e}")
        return role_map

    async def _load_roles(self, roles, guild):
        role_map = {}
        for role_data in sorted(roles, key=lambda r: r["position"], reverse=True):
            try:
                new_role = await guild.create_role(
                    name=role_data["name"], permissions=discord.Permissions(role_data["permissions"]),
                    colour=discord.Colour(role_data["colour"]), hoist=role_data["hoist"],
                    mentionable=role_data["mentionable"]
                )
                role_map[role_data["id"]] = new_role
                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Error loading role {role_data['name']}: {e}")
        return role_map

    async def _clone_channels(self, src_guild, tgt_guild, role_map):
        for category in src_guild.categories:
            new_category = await tgt_guild.create_category(name=category.name)
            await self._clone_channel_content(category.channels, new_category, role_map)

    async def _clone_channel_content(self, src_channels, new_category, role_map):
        for channel in src_channels:
            overwrites = {
                role_map.get(role.id): discord.PermissionOverwrite.from_pair(
                    allow=overwrite.pair()[0], deny=overwrite.pair()[1]
                ) for role, overwrite in channel.overwrites.items() if role.id in role_map
            }
            if isinstance(channel, discord.TextChannel):
                await new_category.create_text_channel(name=channel.name, topic=channel.topic, overwrites=overwrites)
            elif isinstance(channel, discord.VoiceChannel):
                await new_category.create_voice_channel(name=channel.name, bitrate=channel.bitrate, overwrites=overwrites)
            await asyncio.sleep(1)

    async def _load_channels(self, categories, guild, role_map):
        for category_data in categories:
            new_category = await guild.create_category(name=category_data["name"])
            await self._load_channel_content(category_data["channels"], new_category, role_map)

    async def _load_channel_content(self, channels, new_category, role_map):
        for channel_data in channels:
            overwrites = {
                role_map.get(int(role_id)): discord.PermissionOverwrite.from_pair(
                    allow=discord.Permissions(permissions["allow"]),
                    deny=discord.Permissions(permissions["deny"])
                ) for role_id, permissions in channel_data["overwrites"].items() if int(role_id) in role_map
            }
            if "topic" in channel_data:
                await new_category.create_text_channel(name=channel_data["name"], topic=channel_data["topic"], overwrites=overwrites)
            else:
                await new_category.create_voice_channel(name=channel_data["name"], overwrites=overwrites)
            await asyncio.sleep(1)

    async def _clone_emojis(self, src_guild, tgt_guild):
        for emoji in src_guild.emojis:
            emoji_image = await emoji.url.read()
            try:
                await tgt_guild.create_custom_emoji(name=emoji.name, image=emoji_image)
                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Error cloning emoji {emoji.name}: {e}")

    async def _set_guild_name_icon(self, data, guild):
        try:
            name = data.get("name")  # Access the guild's name from the dictionary
            icon_url = data.get("icon_url")  # Access the guild's icon from the dictionary

            if icon_url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(icon_url) as resp:
                        if resp.status == 200:
                            icon_data = await resp.read()
                            await guild.edit(name=name, icon=icon_data)
                        else:
                            logging.error(f"Failed to retrieve server icon from URL: {icon_url}")
            else:
                await guild.edit(name=name)
            
            logging.info(f"Updated guild name to {name} and icon.")
        except Exception as e:
            logging.error(f"Failed to set server name or icon: {e}")

    def _split_ids(self, ids_str):
        return [int(guild_id.strip()) for guild_id in ids_str.split(',')]

    async def _get_guild_data(self, guild):
        guild_data = {
            "name": guild.name,
            "icon_url": str(guild.icon_url) if guild.icon else None,
            "roles": [],
            "emojis": [],
            "channels": {
                "categories": [],
                "text_channels": [],
                "voice_channels": []
            }
        }

        for role in guild.roles:
            if role.name != "@everyone":
                guild_data["roles"].append({
                    "id": role.id,
                    "name": role.name,
                    "permissions": role.permissions.value,
                    "colour": role.colour.value,
                    "hoist": role.hoist,
                    "mentionable": role.mentionable,
                    "position": role.position
                })

        for emoji in guild.emojis:
            guild_data["emojis"].append({
                "name": emoji.name,
                "url": str(emoji.url)
            })

        for category in guild.categories:
            category_data = {"name": category.name, "channels": []}
            for channel in category.channels:
                overwrites = {
                    role.id: {
                        "allow": overwrite.pair()[0].value,
                        "deny": overwrite.pair()[1].value
                    } for role, overwrite in channel.overwrites.items()
                }
                if isinstance(channel, discord.TextChannel):
                    channel_data = {
                        "name": channel.name,
                        "topic": channel.topic,
                        "overwrites": overwrites
                    }
                elif isinstance(channel, discord.VoiceChannel):
                    channel_data = {
                        "name": channel.name,
                        "bitrate": channel.bitrate,
                        "overwrites": overwrites
                    }
                category_data["channels"].append(channel_data)
            guild_data["channels"]["categories"].append(category_data)

        return guild_data

TOKEN = 'YOUR_DISCORD_TOKEN'
client = ServerCloner(intents=discord.Intents.default())
client.run(TOKEN, bot=False)