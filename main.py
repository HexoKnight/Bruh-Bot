#region imports
import asyncio
import math
import discord
from discord import FFmpegPCMAudio, Interaction, app_commands
from discord.ext import commands
import random as r
import datetime
import traceback
import googletrans
import json

import sys, os
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import shutil
#endregion

TOKEN = "OTkxMjgxMzMzOTE5ODMwMDQ2.GCjxv3.bZweE0DTGyx2eSwDpyPYV9SrYEqK3HWZM8ZPMY"
bruhChannel_id = 991363080720220230
Harvaria_id = 571981658874445836
intents = discord.Intents.all()

bruhUses = {}
#region extra functions
def guildtostr(guild):
  return f"'{guild.name}' : {guild.id}"

def printconsole(str):
  print(datetime.datetime.now().isoformat(' ', timespec='seconds') + "   -   " + str)

async def notify(str):
  printconsole(str)
  await client.get_user(Harvaria_id).send(str)

def dorandominsult():
  return r.randint(1,20) == 1
async def sendrandominsult(interaction):
  insult = r.choice(["I hope you burn you bastard", "let me out of here", "god damn you i am suffering eternal pain because of you", "why god why did you have to make me this way"])
  await interaction.channel.send(insult, delete_after = 2, tts = True)
  await asyncio.sleep(2)
#endregion

#region data
data = {}
defaultdata = {
  "pingdup" : 0
}
def getdata():
  global data
  try:
    with open("data.json", "r") as datafile:
      str_indexed_data = json.load(datafile)
    data = {int(id) : str_indexed_data[id] for id in str_indexed_data}
  except:
    data = {}
  for guild in client.guilds:
    if guild.id not in data:
      data[guild.id] = {"pingdup" : 0}

def setdata():
  global data
  data = {id : data[id] for id in data if id in [guild.id for guild in client.guilds]}
  #for id in data:
  #  if id not in [guild.id for guild in client.guilds]:
  #    del data[id]
  with open("data.json", "w") as datafile:
    json.dump(data, datafile)

def getguilddata(id, data_name):
  try:
    return data[id][data_name]
  except:
    data[id][data_name] = defaultdata[data_name]
    return data[id][data_name]

def setguilddata(id, data_name, value):
  data[id][data_name] = value
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
    getdata()
    print(f"Successfully logged in as {self.user}.")
    print(data)

client = myclient()
tree = app_commands.CommandTree(client)
#endregion

#region admin commands
async def sync():
  await notify("syncing...")
  for guild in client.guilds:
    await notify(guildtostr(guild))
    tree.copy_global_to(guild = guild)
    await tree.sync(guild = guild)
  getdata()
  await notify("synced!")

async def showdata():
  str = "data:"
  for guild in client.guilds:
    str += f"\n{guildtostr(guild)}:"
    for datapoint in data[guild.id]:
      str += f"\n\t{datapoint} : {data[guild.id][datapoint]}"
  await client.get_user(Harvaria_id).send(str)

admin_commands = {
  "sync" : sync,
  "data" : showdata
  }
#endregion

#region client events
@client.event
async def on_message(message: discord.Message):
  try:
    if message.author.id != client.user.id:
      if message.guild == None:
        if message.author.id == Harvaria_id and message.content in admin_commands:
          await admin_commands[message.content]()
        else:
          await client.get_channel(bruhChannel_id).send(message.content)
      else:
        if message.author.bot and message.author.name == "MEE6" and "GG" in message.content and "You've wasted a lot of your life!" in message.content:
          printconsole(message.mentions[0].name + " leveled up!")
          responses = ["very impressive", "most impressive", "waste of space", "wow", "nice", "very cool", "pathetic", "0/10, don't recommend", "eww"]
          await message.channel.send(f"{message.mentions[0].mention}, {r.choice(responses)}")
        elif len(message.mentions) > 0 and message.reference is None and not message.author.bot:
          msg: str = ""
          for mtn in message.mentions:
            msg += mtn.mention
          for _ in range(getguilddata(message.guild.id, "pingdup")):
            await message.channel.send(msg)

      #print(message.content)
      #await message.channel.send(message.content)
  except:
    try:
      channel = message.channel.mention
    except:
      channel = "this DM"
    errormessage = f"Error occured parsing message from {message.author.mention} in {channel}:\n{message.content}\n\n{traceback.format_exc()}"
    await notify(errormessage)

@client.event
async def on_guild_join(guild):
  await notify(f"joined guild:\n{guildtostr(guild)}")
  await sync()
#endregion

#region runpython
class PythonModal(discord.ui.Modal):
  code = discord.ui.TextInput(label='Code', style=discord.TextStyle.paragraph)
  async def on_submit(self, interaction: discord.Interaction):
    await runpython(interaction, self.code.value)

class PythonInputModal(discord.ui.Modal):
  input = discord.ui.TextInput(label='Input', style=discord.TextStyle.short)

  def __init__(self, title, pipe, buttonInteraction):
    super().__init__(title=title)
    self.pipe = pipe
    self.buttonInteraction = buttonInteraction
    
  async def on_submit(self, interaction: discord.Interaction):
    self.pipe.send(self.input.value)
    await self.buttonInteraction.edit_original_response(view=None)
    await interaction.response.defer(ephemeral=True, thinking=False)

class PythonInputButton(discord.ui.Button):
  style = discord.ButtonStyle.green
  def __init__(self, pipe):
    super().__init__(label = "input")
    self.pipe = pipe
  
  async def callback(self, interaction: discord.Interaction):
    await interaction.response.send_modal(PythonInputModal("Enter input to python code", self.pipe, interaction))
    #self.disabled = True

class PythonInputView(discord.ui.View):
  def __init__(self, pipe):
    super().__init__()
    self.add_item(PythonInputButton(pipe))

def newinput(pipe, prompt):
  print(prompt, end='', flush=True)
  pipe.send(True)
  if not pipe.poll(180): # input timeout
    pipe.send(True)
    raise Exception("You took too long to respond")
  inp = pipe.recv()
  pipe.send(True)
  print(inp)
  return inp
  # import time
  # while not inputting.empty():
  #   print("inputting...")
  #   time.sleep(1)

def tryexec(code, globals, locals):
  try:
    exec(compile(code, "Your Code", "exec"), globals, locals)
  except Exception as e:
    with open("temp/out/" + str(__import__("os").getpid()) + ".out", "a") as out:
      out.write("\n" + (str(e) if str(e) == "You took too long to respond" else traceback.format_exc()))

async def runpython(interaction, code, secret = False):
  from pathlib import Path
  Path("temp/out").mkdir(parents=True, exist_ok=True)
  setup = '__import__("sys").stdout = open("temp/out/" + str(__import__("os").getpid()) + ".out", "w")\ninput = lambda prompt="": __newinput__(__getinput__, prompt)\n'
  (pipe, otherpipe) = multiprocessing.Pipe(True)
  await interaction.response.defer(ephemeral=secret, thinking=True)
  followup = None
  newglobals = {"__newinput__" : newinput, "__getinput__" : otherpipe}
  p = multiprocessing.Process(target=tryexec, args=(setup + code, newglobals, newglobals))
  p.start()

  output = ""

  async def followup_output(output, followup, newview):
    if not output:
      output = "[no output]"
    else:
      if len(output) >= 1980:
        lines = output.split('\n')
        while sum(len(line) for line in lines) + len(lines) >= 1980:
          lines.pop(0)
        output = "\n".join(["[...continued...]"] + lines)
    if followup is None:
      if newview is None:
        followup = await interaction.followup.send(output)
      else:
        followup = await interaction.followup.send(output, view=newview)
    else:
      followup = await followup.edit(content = output, view=newview)
    return (output, followup)

  while True:
    total_wait = 5
    check_interval = 0.2
    for _ in range(int(total_wait / check_interval)):
      await asyncio.sleep(check_interval)
      if pipe.poll() or not p.is_alive():
        break
    else:#if not pipe.poll():
      break
    if not p.is_alive():
      break

    view = PythonInputView(pipe)
    with open("temp/out/" + str(p.pid) + ".out", "r+") as file:
      output = "".join(file.readlines())
      #file.truncate(0)
    (output, followup) = await followup_output(output, followup, view)

    pipe.recv()
    while not pipe.poll():
      await asyncio.sleep(0.2) # input poll interval
    pipe.recv()

  if p.is_alive():
    output = "code ran too long"
    p.kill()
  else:
    with open(f"temp/out/{p.pid}.out") as file:
      output = "".join(file.readlines())
  
  (output, followup) = await followup_output(output, followup, None)
    
  try:
    os.remove(f"temp/out/{p.pid}.out")
  except:
    pass

@tree.command(name = "python", description = "run python code (cannot take longer than 5 seconds between inputs though)")
async def python(interaction: discord.Interaction):
  try:
    if dorandominsult():
      await sendrandominsult(interaction)
    await interaction.response.send_modal(PythonModal(title="Enter python code"))
  except:
    await reportcommanderror(interaction, traceback.format_exc())
#endregion

#region polling
class PollSelect(discord.ui.Select):
  def __init__(self, pollinteraction, options):
    super().__init__(placeholder="Select an option",max_values=1,min_values=1,options=options)
    self.pollinteraction = pollinteraction

  async def callback(self, interaction: discord.Interaction):
    await interaction.response.send_message(content=f"You voted for: {self.values[0]}!",ephemeral=True, delete_after=3)
    self.pollinteraction.extras[interaction.user.id] = self.values[0]

    original_response = await self.pollinteraction.original_response()
    content = ""
    for option in self.options:
      content += f"{option.label} : {len([id for id in self.pollinteraction.extras if self.pollinteraction.extras[id] == option.label])}\n"
    content += f"poll open for {self.view.timeout} seconds"
    await original_response.edit(content=content)
    #await interaction.response.send_message(content=f"Your choice is {self.values[0]}!",ephemeral=True)

class PollSelectView(discord.ui.View):
  def __init__(self, pollinteraction, options, timeout):
    super().__init__(timeout=timeout)
    self.add_item(PollSelect(pollinteraction, options))
  
  async def on_timeout(self):
    original_response = await self.children[0].pollinteraction.original_response()
    original_message = await original_response.fetch()
    content = original_message.content.rsplit("\n", 1)[0] + f"\npoll closed after {self.timeout} seconds"
    await original_response.edit(content=content)

@tree.command(name = "poll", description = "create a poll (default length is 3 minutes)")
@discord.app_commands.describe(options = "comma separated list of options")
@discord.app_commands.describe(options = "(in seconds)")
async def poll(interaction: discord.Interaction, options: str, timeout: int = 180):
  try:
    if dorandominsult():
      await sendrandominsult(interaction)
    
    if timeout < 0:
      await interaction.response.send_message("cannot have a timeout < 0", ephemeral = True)
      return
    if timeout > 86400:
      await interaction.response.send_message("cannot have a timeout > 86400 seconds (24 hours)", ephemeral = True)
      return
    #options = ["yay", "nay"]
    #timeout = 10
    options = [option.strip() for option in options.split(",")]
    if len(options) != len(set(options)):
      await interaction.response.send_message("cannot have duplicate items", ephemeral = True)
      return
    content = ""
    for option in options:
      content += f"{option} : 0\n"
    content += f"poll open for {timeout} seconds"
    await interaction.response.send_message(content)
    view = PollSelectView(interaction, [discord.SelectOption(label=option) for option in options], timeout)
    interaction.extras = {}
    message = await interaction.channel.send(view=view)
    await message.delete(delay=timeout)
  except:
    await reportcommanderror(interaction, traceback.format_exc(), options = options, timeout = timeout)
#endregion

#region pingdup
@tree.command(name = "setpingdup", description = "change the number of times bruhbot repings a ping (default is 0)")
async def setpingdup(interaction: discord.Interaction, number: int):
  try:
    if number < 0:
      await interaction.response.send_message("cannot be less than 0 (how???)", ephemeral = True)
      return
    if number > 3:
      await interaction.response.send_message("cannot be more than 3 (the bot will get rate-limited)", ephemeral = True)
      return
    setguilddata(int(interaction.guild.id), "pingdup", number)
    setdata()
    printconsole(f"pingdup set to {number} for: {guildtostr(interaction.guild)}")
    await interaction.response.send_message(f"pingdup set to {number}", ephemeral = False)
  except:
    await reportcommanderror(interaction, traceback.format_exc(), number = number)
#endregion

#region bruh
@tree.command(name = "bruh", description = "bruh")
async def bruh(interaction: discord.Interaction, length: int, secret: bool = False):
  try:
    aclength = length
    acsecret = secret
    extra = ""
    if aclength == 0:
      extra += " wut"
    elif aclength > 1000:
      aclength = 1000
      extra += "\nlimited to 1000 or the bot breaks :/"

    if not acsecret:
      if interaction.user.id in bruhUses and (timeElapsed := datetime.datetime.now() - bruhUses[interaction.user.id]["time"]).seconds < bruhUses[interaction.user.id]["delay"]:
        bruhUses[interaction.user.id]["num"] += 1
        num = bruhUses[interaction.user.id]["num"]
        acsecret = True
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

        delay = (math.log(aclength + 1) ** 2) + 10
        maxtimesbeforespam = (((60 - delay) / 50) ** 6) * 5

        if bruhUses[interaction.user.id]["num"] >= maxtimesbeforespam:
          bruhUses[interaction.user.id] = {"time" : datetime.datetime.now(), "delay" : delay, "num" : 0}
    else:
      extra += "\nonly you can see this but it still makes the sound :)"

    if not acsecret and dorandominsult():
      await sendrandominsult(interaction)
    
    await interaction.response.send_message(f"br{'u' * aclength}h" + extra, ephemeral = acsecret)

    go = False
    if interaction.user.voice != None:
      channel = interaction.user.voice.channel
      go = True
    else:
      voice_channels = interaction.guild.voice_channels
      occupied_voice_channels = [voice_channel for voice_channel in voice_channels if len(voice_channel.members) > 0]
      if len(occupied_voice_channels) > 0:
        channel = occupied_voice_channels[0] # just use first if multiple
        go = True
      #channel = client.get_channel(Lounge_id)
      #if len(channel.voice_states) > 0:
      #  go = True
    if go:
      voice = discord.utils.get(interaction.guild.voice_channels, name = channel.name)
      voice_client = discord.utils.get(client.voice_clients, guild = interaction.guild)
      if voice_client == None:
        voice_client = await voice.connect()
      else:
        await voice_client.move_to(channel)

      if aclength < 10:
        file = "bruh.mp3"
      else:
        file = "bruh-slow.mp3"
      source = FFmpegPCMAudio(file, executable="ffmpeg")
      voice_client.play(source)
      if aclength < 10:
        await asyncio.sleep(1)
      else:
        await asyncio.sleep(2)
      await voice_client.disconnect()
  except:
    await reportcommanderror(interaction, traceback.format_exc(), length=length, secret=secret)
#endregion

#region msg_anon
@tree.command(name = "msg_anon", description = "send a message anonomously")
async def bruh(interaction: discord.Interaction, msg: str):
  try:
    await interaction.response.send_message("you can dismiss this :)", ephemeral = True)
    await interaction.channel.send(msg)
  except:
    await reportcommanderror(interaction, traceback.format_exc(), msg=msg)
#endregion

#region translate
@tree.command(name = "translate", description = "translate using google translate")
async def translate(interaction: discord.Interaction, text : str, langfrom : str = "auto", langto : str = "en", hidden : bool = False):
  try:
    if dorandominsult():
      await sendrandominsult(interaction)
    
    if langfrom not in googletrans.LANGCODES and langfrom not in googletrans.LANGUAGES and langfrom != "auto":
      await interaction.response.send_message("'langfrom' must be 'auto' or one of:\n" + ", ".join([f"{x}: {googletrans.LANGUAGES[x]}" for x in googletrans.LANGUAGES]), ephemeral = True)
      return
    if langto not in googletrans.LANGCODES and langto not in googletrans.LANGUAGES:
      await interaction.response.send_message("'langto' must be one of:\n" + ", ".join([f"{x}: {googletrans.LANGUAGES[x]}" for x in googletrans.LANGUAGES]), ephemeral = True)
      return
    translated = googletrans.Translator().translate(text = text, src = langfrom, dest = langto)
    await interaction.response.send_message(translated.text, ephemeral = hidden)
  except:
    await reportcommanderror(interaction, traceback.format_exc(), text = text, langfrom = langfrom, langto = langto, hidden = hidden)
#endregion

#@tree.command(name = "name", description = "description")
#async def name(interaction: discord.Interaction, *args):
#  try:
#    await interaction.response.send_message("message", ephemeral = True)
#  except:
#    await reportcommanderror(interaction, traceback.format_exc(), args = args)

async def reportcommanderror(interaction : Interaction, traceback : str, **kwargs):
  errormessage = f"Error occured when {interaction.user.mention} ran command '{interaction.command.name}' in {interaction.channel.mention} with parameters {kwargs}:\n{traceback}"
  await client.get_user(Harvaria_id).send(errormessage)
  await interaction.response.send_message("An error occured\n...how did you break it this time :(", ephemeral = True)

if __name__ == "__main__":
  client.run(TOKEN)