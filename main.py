#region imports
import asyncio
import discord
from discord import Interaction, app_commands
import random as r
import datetime
import shutil
from pathlib import Path
#endregion

TOKEN = Path("TOKEN").read_text().strip()
bruhChannel_id = 991363080720220230
SuperAdmin = 571981658874445836 # hexoknight8
intents = discord.Intents.all()

with open("insults.txt") as insultsFile:
  insults = [insult.strip() for insult in insultsFile.readlines()]

bruhUses = {}
suspended = False
last_try_sync = None

#region extra functions
def idtostr(id):
  name = "unknown (probably error)"
  if (guild := client.get_guild(id)) is not None:
    name = f"'{guild.name}'"
  elif (user := client.get_user(id)) is not None:
    name = user.mention
  return f"{name} : {id}"
def guildtostr(guild):
  return f"'{guild.name}' : {guild.id}"
def useridtostr(userid):
  return f"'{client.get_user(userid).mention}' : {userid}"

def printconsole(str):
  print(datetime.datetime.now().isoformat(' ', timespec='seconds') + "   -   " + str)

async def notify(userids, str):
  printconsole(str)
  await notifynoprint(userids, str)
async def notifynoprint(userids, str):
  try:
    iterator = iter(set(userids))
  except:
    iterator = iter([userids])
  for userid in iterator:
    await client.get_user(userid).send(str)

def dorandominsult():
  return r.randint(1,20) == 1
async def sendrandominsult(interaction):
  insult = r.choice(insults)
  await interaction.channel.send(insult, delete_after = 2, tts = True)
  await asyncio.sleep(2)
#endregion

#region client/tree setup
class myclient(discord.Client):
  def __init__(self):
    super().__init__(intents=intents)

  async def on_ready(self):
    await self.wait_until_ready()
    try:
      shutil.rmtree("temp")
    except:
      pass
    retrievedata("server")
    retrievedata("admin")
    # await notify(getadmins("restarts") + getadmins("updates"), f"Successfully logged in as {self.user}.")
    print(data)

client = myclient()
tree = app_commands.CommandTree(client)
#endregion

from data import *

from admin_commands import *

#@tree.command(name = "name", description = "description")
#async def name(interaction: discord.Interaction, *args):
#  try:
#    await interaction.response.send_message("message", ephemeral = True)
#  except:
#    await reportcommanderror(interaction, traceback.format_exc(), args = args)

async def reportcommanderror(interaction : Interaction, traceback : str, **kwargs):
  if interaction.command == None:
    errormessage = f"Error occured when {interaction.user.mention} ran an unknown command in {interaction.channel.mention}:\n{traceback}"
  else:
    errormessage = f"Error occured when {interaction.user.mention} ran command '{interaction.command.name}' in {interaction.channel.mention} with parameters {kwargs}:\n{traceback}"
  await notify(getadmins("errors"), errormessage)

  message = "An error occured\n...how did you break it this time :("
  if not interaction.response.is_done():
    await interaction.response.send_message(message, ephemeral = True)
  else:
    original = await interaction.original_response()
    await interaction.edit_original_response(content = original.content + "\n\n" + message)

from user_commands import *

from client_events import *

if __name__ == "__main__":
  client.run(TOKEN)