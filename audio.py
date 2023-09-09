import discord
from discord import FFmpegPCMAudio
import youtube_dl

from __main__ import client

async def playaudio(url: str, user: discord.User, guild: discord.Guild, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'):#, timeout: int = 0):
  channel = None
  member = guild.get_member(user.id)
  if member.voice != None:
    channel = member.voice.channel
  else:
    occupied_voice_channels = [voice_channel for voice_channel in guild.voice_channels if len(voice_channel.members) > 0]
    if len(occupied_voice_channels) > 0:
      channel = occupied_voice_channels[0] # just use first if multiple
  
  if channel is not None:
    voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild = guild)
    if voice_client == None:
      voice = discord.utils.get(guild.voice_channels, name = channel.name)
      voice_client = await voice.connect(timeout=5)
    else:
      if voice_client.channel.id != channel.id:
        await voice_client.move_to(channel)
      elif voice_client.is_playing() and not voice_client.is_paused():
        voice_client.stop()

    try:
      with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
        info = ydl.extract_info(url, download=False)
        url = info['formats'][0]['url']
      #FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    except:
      pass # evidently not youtube link so hopefully direct link

    source = FFmpegPCMAudio(url, executable="ffmpeg", before_options=before_options, options='-vn')
    # wait = asyncio.Event()
    # loop = asyncio.get_running_loop()

    def wait():
      voice_client.disconnect()

    voice_client.play(source)#, after=lambda _: loop.call_soon_threadsafe(wait.set))
    
    # if timeout <= 0:
    #   await wait.wait()
    # else:
    #   try:
    #     await asyncio.wait_for(wait.wait(), timeout)
    #   except:
    #     pass
    # #await voice_client.disconnect()
    # source.cleanup()