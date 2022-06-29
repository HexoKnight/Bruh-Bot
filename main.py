import asyncio
import math
import discord
from discord import FFmpegPCMAudio, app_commands
import random as r
import datetime

TOKEN = "OTkxMjgxMzMzOTE5ODMwMDQ2.GCjxv3.bZweE0DTGyx2eSwDpyPYV9SrYEqK3HWZM8ZPMY"
TheGroup_id = 761690744703942706
bruhChannel_id = 991363080720220230
intents = discord.Intents.all()

bruhUses = {}

class myclient(discord.Client):
  def __init__(self):
    super().__init__(intents=intents)
    self.synced = False

  async def on_ready(self):
    await self.wait_until_ready()
    if not self.synced:
      await tree.sync(guild = discord.Object(id = TheGroup_id))
      self.synced = True
    print(f"Successfully logged in as {self.user}.")

client = myclient()
tree = app_commands.CommandTree(client)

@tree.command(name = "bruh", description = "bruh", guild = discord.Object(TheGroup_id))
async def bruh(interaction: discord.Interaction, length: int, secret: bool = False):
  print(interaction.command.name)
  extra = ""
  if length == 0:
    extra += " wut"
  elif length > 1000:
    length = 1000
    extra += "\nlimited to 1000 or the bot breaks :/"

  if not secret:
    if interaction.user.id in bruhUses and (timeElapsed := datetime.datetime.now() - bruhUses[interaction.user.id]["time"]).seconds < bruhUses[interaction.user.id]["delay"]:
      bruhUses[interaction.user.id]["num"] += 1
      num = bruhUses[interaction.user.id]["num"]
      secret = True
      extra += f"\ncooldown due to spam : {'%.2f' % (bruhUses[interaction.user.id]['delay'] - timeElapsed.seconds)}s"
      if num > 1:
        extra += "\n"
        if num > 7:
          extra += "PSYCH! I'M IMMORTAL HAHAHAHA!"
        elif num > 6:
          extra += "I'M LITERALLY GONNA DIE"
        elif num > 5:
          extra += "YOU'RE KILLING ME BRO"
        elif num > 4:
          extra += "PLZ NO SPAM"
        else:
          extra += "plz no spam"
        if num > 2:
          extra += " (only you can see this :( "
          if num > 3:
            extra += "but it still makes the sound :) "
          extra += ")"
    else:
      if interaction.user.id not in bruhUses:
        bruhUses[interaction.user.id] = {"time" : datetime.datetime.now(), "delay" : 0, "num" : 0}
      if interaction.user.id in bruhUses and bruhUses[interaction.user.id]["delay"] == 0:
        bruhUses[interaction.user.id]["num"] += 1
      
      delay = (math.log(length + 1) ** 2) + 10
      maxtimesbeforespam = (((60 - delay) / 50) ** 6) * 5
  
      if bruhUses[interaction.user.id]["num"] >= maxtimesbeforespam:
        bruhUses[interaction.user.id] = {"time" : datetime.datetime.now(), "delay" : delay, "num" : 0}
  else:
    extra += "\nonly you can see this but it still makes the sound :)"

  await interaction.response.send_message(f"br{'u' * length}h" + extra, ephemeral = secret)
  
  if interaction.user.voice != None:
    channel = interaction.user.voice.channel
    voice = discord.utils.get(interaction.guild.voice_channels, name = channel.name)
    voice_client = discord.utils.get(client.voice_clients, guild = interaction.guild)
    if voice_client == None:
      voice_client = await voice.connect()
    else:
      await voice_client.move_to(channel)
    
    if length < 10:
      file = "bruh.mp3"
    else:
      file = "bruh-slow.mp3"
    source = FFmpegPCMAudio(file, executable="ffmpeg")
    voice_client.play(source)
    if length < 10:
      await asyncio.sleep(1)
    else:
      await asyncio.sleep(2)
    await voice_client.disconnect()


@tree.command(name = "msg_anon", description = "send a message anonomously", guild = discord.Object(TheGroup_id))
async def bruh(interaction: discord.Interaction, msg: str):
  await interaction.response.send_message("you can dismiss this :)", ephemeral = True)
  await interaction.channel.send(msg)

@client.event
async def on_message(message: discord.Message):
  if message.author.id != client.user.id:
    if message.guild == None:
      await client.get_channel(bruhChannel_id).send(message.content)
    else:
      if message.author.bot and message.author.name == "MEE6" and "GG" in message.content and "You've wasted a lot of your life!" in message.content:
        print(message.mentions[0].name + " leveled up!")
        responses = ["very impressive", "most impressive", "waste of space", "wow", "nice", "very cool", "pathetic"]
        await message.channel.send(f"{message.mentions[0].mention}, {r.choice(responses)}")
      elif len(message.mentions) > 0:
        msg: str = ""
        for mtn in message.mentions:
          msg += mtn.mention
        for _ in range(3):
          await message.channel.send(msg)
    
    #print(message.content)
    #await message.channel.send(message.content)

client.run(TOKEN)