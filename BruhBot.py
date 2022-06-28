import asyncio
import discord
from discord import FFmpegPCMAudio, app_commands
import random as r

TOKEN = "OTkxMjgxMzMzOTE5ODMwMDQ2.GCjxv3.bZweE0DTGyx2eSwDpyPYV9SrYEqK3HWZM8ZPMY"
TheGroup_id = 761690744703942706
bruhChannel_id = 991363080720220230
intents = discord.Intents.all()

class myclient(discord.Client):
  def __init__(self):
    super().__init__(intents=intents)
    self.synced = False

  async def on_ready(self):
    await self.wait_until_ready()
    if not self.synced:
      await tree.sync(guild = discord.Object(id = TheGroup_id))#You've wasted a lot of your life!
      self.synced = True
    print(f"We have logged in as {self.user}.")

client = myclient()
tree = app_commands.CommandTree(client)

@tree.command(name = "bruh", description = "bruh", guild = discord.Object(TheGroup_id))
async def bruh(interaction: discord.Interaction, length: int, secret: bool = False):
  await interaction.response.send_message(f"br{'u' * length}h", ephemeral = secret)
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
    
  #  print(message.content)
  #  await message.channel.send(message.content)

client.run(TOKEN)