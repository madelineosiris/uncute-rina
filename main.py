from datetime import datetime  # for startup and crash logging, and Reminders
program_start = datetime.now()  # first startup time datetime; for logging startup duration

from time import mktime  # to convert datetime to unix epoch time to store in database
import discord  # for main discord bot functionality
import json  # for loading the API keys file
import logging  # to set logging level to not DEBUG and hide unnecessary logs
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # for scheduling Reminders
from pymongo.database import Database as pymongodatabase  # for MongoDB database typing
from pymongo import MongoClient
import motor.motor_asyncio as motorasync  # for making Mongo run asynchronously (during api calls)
import motor.core as motorcore  # for typing
import os  # for creating outputs/ directory

from resources.utils.utils import debug, TESTING_ENVIRONMENT  # for logging crash messages
from resources.customs.bot import Bot
from resources.customs.reminders import ReminderObject  # Reminders (/reminders remindme)
from resources.customs.watchlist import get_or_fetch_watchlist_index  # for fetching all watchlists on startup

BOT_VERSION = "1.2.9.21"

EXTENSIONS = [
    "cmd_addons",
    "cmd_ban_appeal_reactions",
    "cmd_compliments",
    "cmd_crashhandling",
    "cmd_customvcs",
    "cmd_emojistats",
    "cmd_help",
    "cmd_getmemberdata",
    #"cmd_pronouns", # depreciated
    "cmd_qotw",
    "cmd_staffaddons",
    "cmd_tags",
    "cmd_termdictionary",
    "cmd_todolist",
    "cmd_toneindicator",
    "cmd_vclogreader",
    "cmd_watchlist",
    "cmd_starboard",
    "cmdg_nameusage",
    "cmdg_reminders",
    #"cmdg_testing_commands",
]


# Permission requirements:
#   server members intent,
#   message content intent,
#   guild permissions:
#       send messages
#       attach files (for image of the member joining graph thing)
#       read channel history (locate previous starboard message, for example)
#       move users between voice channels (custom vc)
#       manage roles (for removing NPA and NVA roles)
#       manage channels (Global: You need this to be able to set the position of CustomVCs in a category, apparently) NEEDS TO BE GLOBAL?
#           Create and Delete voice channels
#       use embeds (for starboard)
#       use (external) emojis (for starboard, if you have external starboard reaction...?)

def get_token_data() -> tuple[str, dict[str, str], pymongodatabase, motorcore.AgnosticDatabase]:
    """
    Ensures the api_keys.json file contains all the bot's required keys, and
    uses these keys to start a link to the MongoDB.

    Returns
    --------
    :class:`tuple[discord_token, other_api_keys, synchronous_db_connection, async_db_connection]`:
        Tuple of discord bot token and database client cluster connections.

    Raises
    -------
    :class:`FileNotFoundError`:
        if the api_keys.json file does not exist.
    :class:`json.decoder.JSONDecodeError`:
        if the api_keys.json file is not in correct JSON format.
    :class:`KeyError`:
        if the api_keys.json file is missing the api key for an api used in the program.
    """
    debug(f"[#+   ]: Loading api keys..." + " " * 30, color="light_blue", end='\r')
    # debug(f"[+     ]: Loading server settings" + " " * 30, color="light_blue", end='\r')
    try:
        with open("api_keys.json", "r") as f:
            api_keys = json.loads(f.read())
        tokens = {}
        bot_token: str = api_keys['Discord']
        missing_tokens: list[str] = []
        for key in ['MongoDB', 'Open Exchange Rates', 'Wolfram Alpha']:
            # copy every other key to new dictionary to check if every key is in the file.
            if key not in api_keys:
                missing_tokens.append(key)
                continue
            tokens[key] = api_keys[key]
    except FileNotFoundError:
        raise
    except json.decoder.JSONDecodeError:
        raise json.decoder.JSONDecodeError(
            "Invalid JSON file. Please ensure it has correct formatting.").with_traceback(None)
    if missing_tokens:
        raise KeyError("Missing API key for: " + ', '.join(missing_tokens))

    debug(f"[##+  ]: Loading database clusters..." + " " * 30, color="light_blue", end='\r')
    cluster: MongoClient = MongoClient(tokens['MongoDB'])
    rina_db: pymongodatabase = cluster["Rina"]
    cluster: motorcore.AgnosticClient = motorasync.AsyncIOMotorClient(tokens['MongoDB'])
    async_rina_db: motorcore.AgnosticDatabase = cluster["Rina"]
    debug(f"[###+ ]: Loading version..." + " " * 30, color="light_blue", end='\r')
    return bot_token, tokens, rina_db, async_rina_db


def get_version() -> str:
    """
    Dumb code for cool version updates. Reads version file and matches with current version string. Updates file if string is newer, and adds another ".%d" for how often the bot has been started in this version.

    Returns
    --------
    :class:`str`:
        Current version/instance of the bot.
    """
    file_version = BOT_VERSION.split(".")
    try:
        os.makedirs("outputs", exist_ok=True)
        with open("outputs/version.txt", "r") as f:
            rina_version = f.read().split(".")
    except FileNotFoundError:
        rina_version = ["0"] * len(file_version)
    # if testing, which environment are you in?
    # 1: private dev server; 2: public dev server (TransPlace [Copy])
    for v in range(len(file_version)):
        if int(file_version[v]) > int(rina_version[v]):
            rina_version = file_version + ["0"]
            break
    else:
        rina_version[-1] = str(int(rina_version[-1]) + 1)
    rina_version = '.'.join(rina_version)
    with open("outputs/version.txt", "w") as f:
        f.write(f"{rina_version}")
    return rina_version


def create_client(tokens: dict, RinaDB: pymongodatabase, asyncRinaDB: motorcore.AgnosticDatabase, version: str) -> Bot:
    debug(f"[#### ]: Loading Bot" + " " * 30, color="light_blue", end='\r')

    intents = discord.Intents.default()
    intents.members = True  #apparently this needs to be additionally defined cause it's not included in Intents.default()?
    intents.message_content = True  #apparently it turned off my default intent or something: otherwise i can't send 1984, ofc.
    #setup default discord bot client settings, permissions, slash commands, and file paths

    debug(f"[#      ]: Loaded bot" + " " * 30, color="green")
    debug(f"[#+     ]: Starting Bot...", color="light_blue", end='\r')
    discord.VoiceClient.warn_nacl = False
    return Bot(
        api_tokens=tokens,
        version=version,
        RinaDB=RinaDB,
        asyncRinaDB=asyncRinaDB,

        intents=intents,
        command_prefix="/!\"@:\\#",
        #  unnecessary, but needs to be set so... uh... yeah. Unnecessary terminal warnings avoided.
        case_insensitive=True,
        activity=discord.Game(name="with slash (/) commands!"),
        allowed_mentions=discord.AllowedMentions(everyone=False)
    )


(TOKEN, tokens, RinaDB, asyncRinaDB) = get_token_data()
version = get_version()
client = create_client(tokens, RinaDB, asyncRinaDB, version)


# region Client events
@client.event
async def on_ready():
    debug(f"[#######]: Logged in as {client.user}, in version {version} (in {datetime.now() - program_start})",
          color="green")
    await client.log_channel.send(f":white_check_mark: **Started Rina** in version {version}")

    debug(f"[+]: Pre-loading all watchlist threads", color="light_blue", end="\r")
    watchlist_channel = client.get_channel(client.custom_ids["staff_watch_channel"])
    if watchlist_channel is not None:  # if running on prod
        await get_or_fetch_watchlist_index(watchlist_channel)
    debug(f"[#]: Loaded watchlist threads." + " " * 15, color="green")


@client.event
async def setup_hook():
    logger = logging.getLogger("apscheduler")
    logger.setLevel(logging.WARNING)
    # remove annoying 'Scheduler started' message on sched.start()
    client.sched = AsyncIOScheduler(logger=logger)
    client.sched.start()

    ## cache server settings into client, to prevent having to load settings for every extension
    debug(f"[##     ]: Started Bot" + " " * 30, color="green")
    ## activate the extensions/programs/code for slash commands

    extension_loading_start_time = datetime.now()
    for extID in range(len(EXTENSIONS)):
        debug(f"[{'#' * extID}+{' ' * (len(EXTENSIONS) - extID - 1)}]: Loading {EXTENSIONS[extID]}" + " " * 15,
              color="light_blue", end='\r')
        await client.load_extension("extensions." + EXTENSIONS[extID])
    debug(f"[###    ]: Loaded extensions successfully (in {datetime.now() - extension_loading_start_time})",
          color="green")

    debug(f"[###+   ]: Loading server settings" + " " * 30, color="light_blue", end='\r')
    try:
        client.log_channel = await client.fetch_channel(988118678962860032)
    except (discord.errors.InvalidData, discord.errors.HTTPException, discord.errors.NotFound,
            discord.errors.Forbidden):  # one of these
        client.running_on_production = False
        if TESTING_ENVIRONMENT == 1:
            client.log_channel = await client.fetch_channel(986304081234624554)
        else:
            client.log_channel = await client.fetch_channel(1062396920187863111)
    client.bot_owner = await client.fetch_user(262913789375021056)  #  (await client.application_info()).owner
    # can't use the commented out code because Rina is owned by someone else in the main server than
    # the dev server (=not me).

    debug(f"[####   ]: Loaded server settings" + " " * 30, color="green")
    debug(f"[####+  ]: Restarting ongoing reminders" + " " * 30, color="light_blue", end="\r")
    collection = RinaDB["reminders"]
    query = {}
    db_data = collection.find(query)
    for user in db_data:
        try:
            for reminder in user['reminders']:
                creationtime = datetime.fromtimestamp(reminder['creationtime'])  #, timezone.utc)
                remindertime = datetime.fromtimestamp(reminder['remindertime'])  #, timezone.utc)
                ReminderObject(client, creationtime, remindertime, user['userID'], reminder['reminder'], user,
                               continued=True)
        except KeyError:
            pass
    debug(f"[#####  ]: Finished setting up reminders" + " " * 30, color="green")
    debug(f"[#####+ ]: Caching bot's command names and their ids", color="light_blue", end='\r')
    commandList = await client.tree.fetch_commands()
    client.commandList = commandList
    debug(f"[###### ]: Cached bot's command names and their ids" + " " * 30, color="green")
    debug(f"[######+]: Starting..." + " " * 30, color="light_blue", end='\r')

    # debug(f"[{'#'*extID}{' '*(len(extensions)-extID-1)} ]: Syncing command tree"+ " "*30,color="light_blue",end='\r')
    # await client.tree.sync()


try:
    client.run(TOKEN, log_level=logging.WARNING)
except SystemExit:
    print("Exited the program forcefully using the kill switch")
# endregion

# region TODO:
# - Translator
# - (Unisex) compliment quotes
# - Add error catch for when dictionaryapi.com is down
# - make more three-in-one commands have optional arguments, explaining what to do if you don't fill in the optional argument

# endregion
