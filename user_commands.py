#region imports
import asyncio
import math
import discord
import datetime
import traceback
import googletrans

import os
import multiprocessing
from pathlib import Path

from typing import Optional
#endregion

from __main__ import client, tree, bruhUses, suspended
from __main__ import dorandominsult, sendrandominsult, reportcommanderror, printconsole, guildtostr
from data import *
from audio import playaudio

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

def tryexec(code, globals, locals):
  try:
    exec(compile(code, "Your Code", "exec"), globals, locals)
  except Exception as e:
    with open("temp/out/" + str(__import__("os").getpid()) + ".out", "a") as out:
      out.write("\n" + (str(e) if str(e) == "You took too long to respond" else traceback.format_exc()))

async def runpython(interaction, code, secret = False):
  if suspended:
    return
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
      await followup.add_reaction('🐍')
    else:
      followup = await followup.edit(content = output, view=newview)
    return (output, followup)

  while True:
    total_wait = 5
    check_interval = 0.1
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
      await asyncio.sleep(0.1) # input poll interval
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
  if suspended:
    return
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
@tree.command(name = "setpingdup", description = "change the number of times bruhbot repings a ping in this server (default is 0)")
async def setpingdup(interaction: discord.Interaction, number: int):
  if suspended:
    return
  try:
    if number < 0:
      await interaction.response.send_message("cannot be less than 0 (how???)", ephemeral = True)
      return
    if number > 3:
      await interaction.response.send_message("cannot be more than 3 (the bot will get rate-limited)", ephemeral = True)
      return
    setdata("server", int(interaction.guild.id), "pingdup", number)
    storedata("server")
    printconsole(f"pingdup set to {number} for: {guildtostr(interaction.guild)}")
    await interaction.response.send_message(f"pingdup set to {number}", ephemeral = False)
  except:
    await reportcommanderror(interaction, traceback.format_exc(), number = number)
#endregion

#region bruh
@tree.command(name = "bruh", description = "bruh")
async def bruh(interaction: discord.Interaction, length: int, secret: bool = False):
  if suspended:
    return
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

    if aclength < 10:
      file = "bruh.mp3"
      timeout = 1
    else:
      file = "bruh-slow.mp3"
      timeout = 2

    await playaudio(file, interaction.user, interaction.guild, '')#, timeout)
    if aclength < 10:
      await asyncio.sleep(1)
    else:
      await asyncio.sleep(2)
    
    voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild = interaction.guild)
    if voice_client != None and voice_client.is_connected():
      await voice_client.disconnect()

      # if aclength < 10:
      #   file = "bruh.mp3"
      # else:
      #   file = "bruh-slow.mp3"
      # source = FFmpegPCMAudio(file, executable="ffmpeg")
      # voice_client.play(source)
      # if aclength < 10:
      #   await asyncio.sleep(1)
      # else:
      #   await asyncio.sleep(2)
      # await voice_client.disconnect()
  except:
    await reportcommanderror(interaction, traceback.format_exc(), length=length, secret=secret)
#endregion

#region msg_anon
@tree.command(name = "msg_anon", description = "send a message anonomously")
async def bruh(interaction: discord.Interaction, msg: str):
  if suspended:
    return
  try:
    await interaction.response.send_message("you can dismiss this :)", ephemeral = True)
    await interaction.channel.send(msg)
  except:
    await reportcommanderror(interaction, traceback.format_exc(), msg=msg)
#endregion

#region translate
@tree.command(name = "translate", description = "translate using google translate")
async def translate(interaction: discord.Interaction, text : str, langfrom : str = "auto", langto : str = "en", hidden : bool = False):
  if suspended:
    return
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

#region cool command
@tree.command(name = "amicool", description = "tells you if you're cool")
async def amicool(interaction: discord.Interaction):
  if suspended:
    return
  if interaction.user.id in data["admin"]:
    await interaction.response.send_message("You are very cool :)")
    message = await interaction.original_response()
    await message.add_reaction('👍')
    await message.add_reaction('😎')
    await message.add_reaction('🙀')
  else:
    await interaction.response.send_message("You are not cool :(")
    message = await interaction.original_response()
    await message.add_reaction('😦')
    await message.add_reaction('🙁')
    await message.add_reaction('☹')
#endregion

#region audio playing
#region play
@tree.command(name = "play", description = "resume playing or play audio file (upload a file or enter a url)")
@discord.app_commands.describe(file = "upload file")
@discord.app_commands.describe(url = "enter url")
async def play(interaction: discord.Interaction, file: Optional[discord.Attachment] = None, url: str = None):
  if suspended:
    return
  try:
    if file is None and url is None:
      voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild = interaction.guild)
      if voice_client == None or not (voice_client.is_playing() or voice_client.is_paused()):
        await interaction.response.send_message(f"Nothing is playing!\neither upload a file or enter a url to start playing something new", ephemeral=True)
      elif voice_client != None and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message(f"resumed playing", ephemeral=False)
      elif voice_client != None and voice_client.is_playing():
        await interaction.response.send_message(f"already playing something!\neither upload a file or enter a url to start playing something new", ephemeral=True)
      return
    # if file.content_type not in ["audio", "video"]:
    #   await interaction.response.send_message(f"not a valid audio source", ephemeral=True)
    #   return
    await interaction.response.send_message(f"playing '{file.filename if file is not None else url}'", ephemeral=False)
    await playaudio(file.url if file is not None else url, interaction.user, interaction.guild)
  except:
    await reportcommanderror(interaction, traceback.format_exc(), file = file) # fix not suspended
#endregion

#region pause
@tree.command(name = "pause", description = "pause the currently playing audio")
async def pause(interaction: discord.Interaction):
  if suspended:
    return
  try:
    voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild = interaction.guild)
    if voice_client == None:
      await interaction.response.send_message(f"not currently playing anything!", ephemeral=True)
    elif voice_client.is_paused():
      await interaction.response.send_message(f"already paused!", ephemeral=True)
    else:
      voice_client.pause()
      await interaction.response.send_message(f"paused playing", ephemeral=False)
  except:
    await reportcommanderror(interaction, traceback.format_exc()) # fix not suspended
#endregion

#region stop
@tree.command(name = "stop", description = "stop the currently playing audio")
async def stop(interaction: discord.Interaction):
  if suspended:
    return
  try:
    voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild = interaction.guild)
    if voice_client == None:
      await interaction.response.send_message(f"not currently playing anything!", ephemeral=True)
      return
    voice_client.stop()
    voice_client.cleanup()
    await voice_client.disconnect()
    await interaction.response.send_message(f"stopped audio", ephemeral=False)
  except:
    await reportcommanderror(interaction, traceback.format_exc()) # fix not suspended
#endregion

#region disconnect
@tree.command(name = "disconnect", description = "disconnect bruhbot from vc")
async def disconnect(interaction: discord.Interaction):
  if suspended:
    return
  try:
    voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild = interaction.guild)
    if voice_client == None:
      await interaction.response.send_message(f"not in vc!", ephemeral=True)
      return
    voice_client.stop()
    voice_client.cleanup()
    await voice_client.disconnect()
    await interaction.response.send_message(f"disconnected bruhbot from vc", ephemeral=False)
  except:
    await reportcommanderror(interaction, traceback.format_exc()) # fix not suspended
#endregion

#endregion

#region tempping
@tree.command(name = "tempping", description = "pings temporarily")
async def tempping(interaction: discord.Interaction, member: discord.Member, time: int = 1):
  if suspended:
    return
  try:
    if member not in interaction.guild.members:
      await interaction.response.send_message("specified user is not in this server", ephemeral = True)
    await interaction.response.send_message(member.mention, ephemeral = False, delete_after = time)
    # await interaction.response.send_message("done 👍", ephemeral = True)
    # await interaction.response.defer()
  except:
    await reportcommanderror(interaction, traceback.format_exc(), member = member, time = time)
#endregion

#region advertise
@tree.command(name = "advertise", description = "advertises")
async def advertise(interaction: discord.Interaction):
  if suspended:
    return
  try:
    await interaction.response.send_message("https://HexoKnight.github.io\n:) get advertised noobs", ephemeral = False)
  except:
    await reportcommanderror(interaction, traceback.format_exc())
#endregion
