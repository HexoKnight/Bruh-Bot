import discord
import random as r
import datetime
import traceback

from main import bruhChannel_id, client, suspended, last_try_sync
from main import printconsole, reportcommanderror
from admin_commands import *

@client.event
async def on_message(message: discord.Message):
  try:
    if message.author.id != client.user.id:
      if message.guild == None:
        if message.content.startswith('!'):
          split = message.content[1:].split()
          if suspended:
            if message.author.id in data["admin"] and split[0] == "unsuspend":
              await unsuspend(message.author.id, *split[1:])
          else:
            if message.author.id in data["admin"] and split[0] in admin_commands:
              await admin_commands[split[0]](message.author.id, *split[1:])
            elif message.author.id == SuperAdmin and split[0] in superadmin_commands:
              await superadmin_commands[split[0]](*split[1:])
        elif not suspended:
          await client.get_channel(bruhChannel_id).send(message.content)
      elif not suspended:
        if message.author.bot and message.author.name == "MEE6" and "GG" in message.content and "You've wasted a lot of your life!" in message.content:
          printconsole(message.mentions[0].name + " leveled up!")
          responses = ["very impressive", "most impressive", "waste of space", "wow", "nice", "very cool", "pathetic", "0/10, don't recommend", "eww"]
          await message.channel.send(f"{message.mentions[0].mention}, {r.choice(responses)}")
        elif len(message.mentions) > 0 and message.reference is None and not message.author.bot:
          msg: str = ""
          for mtn in message.mentions:
            msg += mtn.mention
          for _ in range(getdata("server", message.guild.id, "pingdup")):
            await message.channel.send(msg)

      #print(message.content)
      #await message.channel.send(message.content)
  except:
    try:
      channel = message.channel.mention
    except:
      channel = "this DM"
    errormessage = f"Error occured parsing message from {message.author.mention} in {channel}:\n{message.content}\n\n{traceback.format_exc()}"
    await notify(getadmins("errors"), errormessage)

@client.event
async def on_guild_join(guild):
  await notify(getadmins("joins"), f"joined guild:\n{guildtostr(guild)}")
  await sync()

@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
  voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild = member.guild)
  if voice_client != None and before.channel is not None and before.channel.id == voice_client.channel.id and len(voice_client.channel.members) == 1:
    await voice_client.stop()
    await voice_client.cleanup()
    await voice_client.disconnect()

@tree.error
async def on_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
  await reportcommanderror(interaction, traceback.format_exc())
  if last_try_sync == None or (datetime.datetime.now() - last_try_sync).seconds > 600: # only try to sync max once every 10 minutes
    await sync(None)