import asyncio
import sys, os
import subprocess

from __main__ import tree, SuperAdmin
from __main__ import idtostr, notify, notifynoprint, guildtostr
import __main__ as main
from data import *

async def sync(userid, *_):
  await notify(getadmins("syncs", userid), "syncing...")
  for guild in client.guilds:
    await notify(getadmins("syncs", userid), guildtostr(guild))
    tree.copy_global_to(guild = guild)
    await tree.sync(guild = guild)
  retrievedata("server")
  await notify(getadmins("syncs", userid), "synced!")

async def showdata(userid, *datanames):
  if not datanames or datanames[0] == "all":
    datanames = [dataname for dataname in data if not dataname.endswith("_default")]
  invalid = ""
  str = ""
  for dataname in datanames:
    if dataname in ["servers", "guild", "guilds", "serverdata", "guilddata"]:
      dataname = "server"
    elif dataname in ["admins", "admindata"]:
      dataname = "admin"
    elif dataname not in data:
      invalid += f"\ninvalid dataname - '{dataname}'"
      continue
    
    str += f"\n{dataname} data:"
    for id in data[dataname]:
      str += f"\n{idtostr(id)}:"
      for datapoint in data[dataname + "_default"]:
        str += f"\n\t{datapoint} : {getdata(dataname, id, datapoint)}"
  if invalid:
    await client.get_user(userid).send(invalid)
  if str:
    await client.get_user(userid).send(str)

async def showadminsettings(userid, *settings):
  if not settings or settings[0] == "all":
    settings = data["admin_default"].keys()
  invalid = ""
  str = ""
  for setting in settings:
    if setting not in data["admin_default"].keys():
      invalid += f"\ninvalid setting - '{setting}'"
      continue
    str += f"\n{setting} - {getdata('admin', userid, setting)}"
  if invalid:
    await client.get_user(userid).send(invalid + "\nuse '!settings all' to see all valid settings")
  if str:
    await client.get_user(userid).send("current settings:" + str)

async def toggleadminsettings(userid, *settings):
  invalid = ""
  str = ""
  for setting in settings:
    setting = setting.strip()
    if setting not in data["admin_default"].keys():
      invalid += f"\ninvalid setting - '{setting}'"
      continue
    current = getdata("admin", userid, setting)
    setdata("admin", userid, setting, not current)
    str += f"\n{setting} to {not current}"
  storedata("admin")
  if invalid:
    await client.get_user(userid).send(invalid + "\nuse '!settings all' to see all valid settings")
  if str:
    await client.get_user(userid).send("toggled:" + str)

async def showhelp(userid, *_):
  str = '''available commands:
!help - display this message
!settings [s|s1 s2...|all] - show your admin settings (specific/multiple/all)
!toggle [s|s1 s2...] - toggle 1 or more admin settings
!data [server|admin|all] - show data for servers/admins/all
!sync - sync bruhbot commands
!restart - restart bruhbot
!update - update bruhbot from the github repo
!suspend - suspend bruhbot (used to disable cloud bruhbot while a local one is being tested)
!unsuspend - unsuspend bruhbot'''
  await client.get_user(userid).send(str)

async def restart(userid, *_):
  await notify(getadmins("restarts", userid), "restarting...")
  future = asyncio.run_coroutine_threadsafe(client.close(), asyncio.get_event_loop())
  future.add_done_callback(lambda _: os.execv(sys.executable, [sys.executable] + sys.argv))

async def update(userid, *params):
  force = "force" in params or "f" in params
  await notify(getadmins("updates", userid), "updating...")
  os.system("git fetch")
  if force:
    await notify(getadmins("updates", userid), "hard reseting repo to remote...")
    update_process = subprocess.run(["git", "reset", "--hard", "origin/main"], capture_output = True, text = True)
  else:
    update_process = subprocess.run(["git", "merge", "--ff-only"], capture_output = True, text = True)
  process_output = update_process.stdout.strip()
  process_error = update_process.stderr.strip()
  if process_error != "":
    process_output += "\n" + process_error
  print(process_output)
  do_restart = True
  allow_force = False
  if force:
    update_output = process_output.split('\n')
  elif process_output.strip().count == 0 or "aborting" in process_output.lower():
    update_output = process_output.split('\n')
    do_restart = False
    allow_force = True
  elif "Already up to date." in process_output:
    update_output = process_output.split('\n')
    do_restart = False
  else:
    update_output = []
    merge = False
    for line in process_output.split('\n'):
      if merge:
        update_output.append(line)
        if "files changed" in line or "file changed" in line:
          break
      elif "Updating" in line:
        update_output.append(line)
        merge = True
    if len(update_output) == 0:
      update_output = process_output.split('\n')
      do_restart = False
      allow_force = True
  
  message = "```\n" + "\n".join(update_output) + "\n```"
  if allow_force:
    message += "\nuse `!update force` to `git reset --hard origin/main` the repo to force an update"
  await notifynoprint(getadmins("updates", userid), message)

  if sys.platform.startswith('win'):
    os.system("pip install -r requirements.txt | findstr -v \"already satisfied\"")
  elif sys.platform.startswith('linux'):
    os.system("pip install -r requirements.txt | grep -v 'already satisfied'")
  else:
    os.system("pip install -r requirements.txt")
  
  if do_restart:
    await restart(userid)

async def suspend(userid, *_):
  if main.suspended:
    await client.get_user(userid).send("already suspended!")
  else:
    main.suspended = True
    await notify(getadmins("suspensions", userid), "suspended!")
async def unsuspend(userid, *_):
  if main.suspended:
    main.suspended = False
    await notify(getadmins("suspensions", userid), "unsuspended!")
  else:
    await client.get_user(userid).send("not suspended!")

async def addadmin(*userids):
  for userid in userids:
    data["admin"][int(userid)] = {}
    await client.get_user(int(userid)).send("you are now an admin of bruhbot (aka a cool person), type !help in this DM for command info")
    await client.get_user(SuperAdmin).send(client.get_user(int(userid)).mention + " is now an admin of bruhbot")
  storedata("admin")
async def removeadmin(*userids):
  for userid in userids:
    del data["admin"][int(userid)]
    await client.get_user(int(userid)).send("you are no longer an admin of bruhbot (aka a cool person) :(")
    await client.get_user(SuperAdmin).send(client.get_user(int(userid)).mention + " is no longer an admin of bruhbot")
  storedata("admin")

admin_commands = {
  "sync" : sync,
  "data" : showdata,
  "settings" : showadminsettings,
  "toggle" : toggleadminsettings,
  "togglesettings" : toggleadminsettings,
  "help" : showhelp,
  "restart" : restart,
  "update" : update,
  "suspend" : suspend,
  "unsuspend" : unsuspend
  }
superadmin_commands = {
  "addadmin" : addadmin,
  "removeadmin" : removeadmin
  }