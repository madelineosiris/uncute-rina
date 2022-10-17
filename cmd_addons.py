import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *

import pymongo # for online database
from pymongo import MongoClient

import random # for picking a random call_cute quote

import asyncio # for waiting a few seconds before removing a timed-out pronoun-selection message

class Addons(commands.Cog):
    def __init__(self, client):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB

    @app_commands.command(name="say",description="Force Rina to repeat your wise words")
    @app_commands.describe(text="What will you make Rina repeat?")
    async def say(self, itx: discord.Interaction, text: str):
        if not isAdmin(itx):
            await itx.response.send_message("Hi. sorry.. It would be too powerful to let you very cool person use this command.",ephemeral=True) #todo
            return
        collection = RinaDB["guildInfo"]
        query = {"guild_id": itx.guild.id}
        guild = collection.find_one(query)
        if guild is None:
            debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!",color="red")
            return
        try:
            vcLog      = guild["vcLog"]
            logChannel = itx.guild.get_channel(vcLog)
            await logChannel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) said a message using Rina: {text}", allowed_mentions=discord.AllowedMentions.none())
            text = text.replace("[[\\n]]","\n").replace("[[del]]","")
            await itx.channel.send(f"{text}", allowed_mentions=discord.AllowedMentions.none())
        except discord.Forbidden:
            await itx.response.send_message("Forbidden! I can't send a message in this channel/thread because I can't see it or because I'm not added to it yet!\n(Add me to the thread by mentioning me, or let Rina see this channel)",ephemeral=True)
            return
        except:
            await itx.response.send_message("Oops. Something went wrong!",ephemeral=True)
            raise
        await itx.response.send_message("Successfully sent!", ephemeral=True)


    @app_commands.command(name="compliment", description="Complement someone fem/masc/enby")
    @app_commands.describe(user="Who do you want to compliment?")
    async def compliment(self, itx: discord.Interaction, user: discord.User):
        # await itx.response.send_message("This command is currently disabled for now, since we're missing compliments. Feel free to suggest some, and ping @MysticMia#7612",ephemeral=True)
        # return

        try:
            user.roles
        except AttributeError:
            itx.response.send_message("Aw man, it seems this person isn't in the server. I wish I could compliment them but they won't be able to see it!",ephemeral=True)
            return
        async def call(itx, user, type):
            quotes = {
                "fem_quotes" : [
                    "Was the sun always this hot? or is it because of you?",
                    "Hey baby, are you an angel? Cuz I’m allergic to feathers.",
                    "I bet you sweat glitter.",
                    "Your hair looks stunning!",
                    "Being around you is like being on a happy little vacation.",
                    "Good girll",
                    "Who's a good girl?? You are!!",
                    "Amazing! Perfect! Beautiful! How **does** she do it?!",
                    "I can tell that you are a very special and talented girl!",
                ],
                "masc_quotes" : [
                    "You are the best man out there.",
                    "You are the strongest guy I know.",
                    "You have an amazing energy!",
                    "You seem to know how to fix everything!",
                    "Waw, you seem like a very attractive guy!",
                    "Good boyy!",
                    "Who's a cool guy? You are!!",
                    "I can tell that you are a very special and talented guy!",

                ],
                "they_quotes" : [
                    "I can tell that you are a very special and talented person!",
                    "Their, their... ",
                ],
                "it_quotes" : [
                    "I bet you do the crossword puzzle in ink!",
                ],
                "unisex_quotes" : [ #unisex quotes are added to each of the other quotes later on.
                    "_Let me just hide this here-_ hey wait, are you looking?!",
                    "Would you like a hug?",
                    "Hey I have some leftover cookies.. \\*wink wink\\*",
                    "Would you like to walk in the park with me? I gotta walk my catgirls",
                    "morb",
                    "You look great today!",
                    "You light up the room!",
                    "On a scale from 1 to 10, you’re an 11!",
                    'When you say, “I meant to do that,” I totally believe you.',
                    "You should be thanked more often. So thank you!",
                    "You are so easy to have a conversation with!",
                    "Ooh you look like a good candidate for my pet blahaj!",



                ]
            }
            type = {
                "she/her"   : "fem_quotes",
                "he/him"    : "masc_quotes",
                "they/them" : "they_quotes",
                "it/its"    : "it_quotes",
                "unisex"    : "unisex_quotes", #todo
            }[type]

            for x in quotes:
                if x == "unisex_quotes":
                    continue
                else:
                    quotes[x] += quotes["unisex_quotes"]

            base = f"{itx.user.mention} complimented {user.mention}!\n"
            if itx.response.is_done():
                # await itx.edit_original_response(content=base+random.choice(quotes[type]), view=None)
                await itx.followup.send(content=base+random.choice(quotes[type]), allowed_mentions=discord.AllowedMentions(everyone=False, users=[user], roles=False, replied_user=False))
            else:
                await itx.response.send_message(base+random.choice(quotes[type]), allowed_mentions=discord.AllowedMentions(everyone=False, users=[user], roles=False, replied_user=False))
                #todo check if pings work
        async def confirm_gender():
            # Define a simple View that gives us a confirmation menu
            class Confirm(discord.ui.View):
                def __init__(self, timeout=None):
                    super().__init__()
                    self.value = None
                    self.timeout = timeout

                # When the confirm button is pressed, set the inner value to `True` and
                # stop the View from listening to more input.
                # We also send the user an ephemeral message that we're confirming their choice.
                @discord.ui.button(label='She/Her', style=discord.ButtonStyle.green)
                async def feminine(self, itx: discord.Interaction, button: discord.ui.Button):
                    self.value = "she/her"
                    await itx.response.edit_message(content='Selected She/Her pronouns for compliment', view=None)
                    self.stop()

                @discord.ui.button(label='He/Him', style=discord.ButtonStyle.green)
                async def masculine(self, itx: discord.Interaction, button: discord.ui.Button):
                    self.value = "he/him"
                    await itx.response.edit_message(content='Selected He/Him pronouns for the compliment', view=None)
                    self.stop()

                @discord.ui.button(label='They/Them', style=discord.ButtonStyle.green)
                async def enby_them(self, itx: discord.Interaction, button: discord.ui.Button):
                    self.value = "they/them"
                    await itx.response.edit_message(content='Selected They/Them pronouns for the compliment', view=None)
                    self.stop()

                @discord.ui.button(label='It/Its', style=discord.ButtonStyle.green)
                async def enby_its(self, itx: discord.Interaction, button: discord.ui.Button):
                    self.value = "it/its"
                    await itx.response.edit_message(content='Selected It/Its pronouns for the compliment', view=None)
                    self.stop()

                @discord.ui.button(label='Unisex/Unknown', style=discord.ButtonStyle.grey)
                async def unisex(self, itx: discord.Interaction, button: discord.ui.Button):
                    self.value = "unisex"
                    await itx.response.edit_message(content='Selected Unisex/Unknown gender for the compliment', view=None)
                    self.stop()

            view = Confirm(timeout=30)
            await itx.response.send_message(f"{user.mention} doesn't have any pronoun roles! Which pronouns would like to use for the compliment?", view=view,ephemeral=True)
            await view.wait()
            if view.value is None:
                await itx.edit_original_response(content=':x: Timed out...', view=None)
                # await asyncio.sleep(3)
                # await itx.delete_original_response()
            else:
                await call(itx, user, view.value)

        roles = ["he/him","she/her","they/them","it/its"]
        userroles = user.roles[:]
        random.shuffle(userroles) # pick a random order for which pronoun role to pick
        for role in userroles:
            if role.name.lower() in roles:
                await call(itx, user, role.name.lower())
                return
        await confirm_gender()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        #random cool commands
        if self.client.user.mention in message.content.split():
            msg = message.content.lower()
            if ((("cute" or "cutie" in msg) and "not" in msg) or "uncute" in msg) and "not uncute" not in msg:
                await message.add_reaction("<:this:960916817801535528>")
            elif "cutie" in msg or "cute" in msg:
                responses = [
                    "I'm not cute >_<",
                    "I'm not cute! I'm... Tough! Badass!",
                    "Nyaa~",
                    "Who? Me? No you're mistaken.",
                    "I very much deny the cuteness of someone like myself",
                    "If you think I'm cute, then you must be uber-cute!!",
                    "I don't think so.",
                    "Haha. Good joke. Tell me another tomorrow",
                    "Ehe, cutie what do u need help with?",
                    "No, I'm !cute.",
                    "You too!",
                    "No, you are <3",
                    "[shocked] Wha- w. .. w what?? .. NOo? no im nott?\nwhstre you tslking about?",
                    "Oh you were talking to me? I thought you were talking about everyone else here,",
                    "Nope. I doubt it. There's no way I can be as cute as you",
                    "Maybe.. Maybe I am cute.",
                    "If the sun was dying, would you still think I was cute?",
                    "Awww. Thanks sweety, but you've got the wrong number",
                    ":joy: You *reaaally* think so? You've gotta be kidding me.",
                    "If you're gonna be spamming this, .. maybe #general isn't the best channel for that.",
                    "You gotta praise those around you as well. "+(message.author.nick or message.author.name)+", for example, is very cute.",
                    "Oh by the way, did I say "+(message.author.nick or message.author.name)+" was cute yet? I probably didn't. "+(message.author.nick or message.author.name)+"? You're very cute",
                    "Such nice weather outside, isn't it? What- you asked me a question?\nNo you didn't, you're just talking to youself.",
                    "".join(random.choice("acefgilrsuwnopacefgilrsuwnopacefgilrsuwnop;;  ") for i in range(random.randint(10,25))), # 3:2 letters to symbols
                    "Oh I heard about that! That's a way to get randomized passwords from a transfem!",
                    "Cuties are not gender-specific. For example, my cat is a cutie!\nOh wait, species aren't the same as genders. Am I still a catgirl then? Trans-species?",
                    "...",
                    "Hey that's not how it works!",
                    "Hey my lie detector said you are lying.",
                    "You know i'm not a mirror, right?",
                    "*And the oscar for cutest responses goes to..  YOU!!*",
                    "No I am not cute",
                    "k",
                    (message.author.nick or message.author.name)+", stop lying >:C",
                    "BAD!",
                    "You're also part of the cuties set",
                    "https://cdn.discordapp.com/emojis/920918513969950750.webp?size=4096&quality=lossless",
                    "[Checks machine]; Huh? Is my lie detector broken? I should fix that..",
                    "Hey, you should be talking about yourself first! After all, how do you keep up with being such a cutie all the time?"]
                respond = random.choice(responses)
                if respond == "BAD!":
                    await message.channel.send("https://cdn.discordapp.com/emojis/902351699182780468.gif?size=56&quality=lossless", allowed_mentions=discord.AllowedMentions.none())
                await message.channel.send(respond, allowed_mentions=discord.AllowedMentions.none())
            else:
                await message.channel.send("I use slash commands! Use /command  and see what cool things might pop up! or something\nPS: If you're trying to call me cute: no, i'm not", delete_after=8)

    @app_commands.command(name="roll", description="Roll a die or dice with random chance!")
    @app_commands.describe(dice="How many dice do you want to roll?",
                           faces="How many sides does every die have?",
                           mod="Do you want to add a modifier? (add 2 after rolling the dice)",
                           advanced="Roll more advanced! example: 1d20+3cs>10. Overwrites dice/faces given; 'help' for more")
    async def roll(self, itx: discord.Interaction, dice: int, faces: int, public: bool=False, mod: int = None, advanced: str = None):
        if advanced is None:
            if dice < 1 or faces < 1:
                await itx.response.send_message("You can't have negative dice/faces! Please give a number above 0",ephemeral=True)
                return
            if dice > 1000000:
                await itx.response.send_message(f"Sorry, if I let you roll `{thousandSpace(dice,separator=',')}` dice, then the universe will implode, and Rina will stop responding to commands. Please stay below 1 million dice...",ephemeral=True)
                return
            if faces > 1000000:
                await itx.response.send_message(f"Uh.. At that point, you're basically rolling a sphere. Even earth has fewer faces than `{thousandSpace(faces,separator=',')}`. Please bowl with a sphere of fewer than 1 million faces...",ephemeral=True)
            rolls = []
            for die in range(dice):
                rolls.append(random.randint(1,faces))
            out = ""
            if mod is None:
                if dice == 1:
                    out = f"I rolled {dice} di{'c'*(dice>1)}e with {faces} face{'s'*(faces>1)}: "+\
                    f"{str(sum(rolls))}"
                else:
                    out = f"I rolled {dice} di{'c'*(dice>1)}e with {faces} face{'s'*(faces>1)}:\n"+\
                    f"{' + '.join([str(roll) for roll in rolls])}  =  {str(sum(rolls))}"
            else:
                out = f"I rolled {dice} {'die' if dice == 0 else 'dice'} with {faces} face{'s'*(faces>1)} and a modifier of {mod}:\n"+\
                f"({' + '.join([str(roll) for roll in rolls])}) + {mod}  =  {str(sum(rolls)+mod)}"
            if len(out) > 1995:
                out = f"I rolled {thousandSpace(dice,separator=',')} {'die' if dice == 0 else 'dice'} with {thousandSpace(faces,separator=',')} face{'s'*(faces>1)}"+f" and a modifier of {thousandSpace(mod or 0,separator=',')}"*(mod is not None)+":\n"+\
                f"With this many numbers, I've simplified it a little. You rolled `{thousandSpace(str(sum(rolls)+(mod or 0)),separator=',')}`."
                rollDb = {}
                for roll in rolls:
                    try:
                        rollDb[roll] += 1
                    except KeyError:
                        rollDb[roll] = 1
                rollDb = dict(sorted(rollDb.items()))
                details = "You rolled "
                for roll in rollDb:
                    details += f"'{roll}'x{rollDb[roll]}, "
                if len(details) > 1500:
                    details = ""
                elif len(details) > 300:
                    public = False
                out = out + "\n" + details
            elif len(out) > 300:
                public = False
            await itx.response.send_message(out,ephemeral=not public)
        else:
            await itx.response.send_message("```\n"+\
            "I rolled nothing. This feature is in development!, sorryyy"+\
            "```",ephemeral=True)


async def setup(client):
    await client.add_cog(Addons(client))
