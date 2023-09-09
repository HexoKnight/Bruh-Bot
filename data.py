import json
from pathlib import Path

from __main__ import client

#region data
data = {
  "server" : {},
  "server_default" : {
    "pingdup" : 0
  },
  "admin" : {},
  "admin_default" : { # must all be booleans for now
    "errors" : False,
    "joins" : False,
    "restarts" : False,
    "updates" : False,
    "syncs" : False,
    "suspensions" : False
  }
}
#endregion

#region data functions
def loadjson(filename):
  try:
    with open(f"data/{filename}.json", "r") as datafile:
      str_indexed_data = json.load(datafile)
    data = {int(id) : str_indexed_data[id] for id in str_indexed_data}
  except:
    data = {}
  return data
def storejson(filename, data):
  Path("data").mkdir(parents=True, exist_ok=True)
  with open(f"data/{filename}.json", "w") as datafile:
    json.dump(data, datafile)

def retrievedata(dataname):
  global data
  data[dataname] = loadjson(dataname)
  if dataname == "server":
    for guild in client.guilds:
      if guild.id not in data["server"]:
        data["server"][guild.id] = {}
def storedata(dataname):
  global data
  thisdata = data[dataname].copy()
  if dataname == "server":
    thisdata = {id : thisdata[id] for id in thisdata if id in [guild.id for guild in client.guilds]}
  storejson(dataname, thisdata)

def getdata(dataname, id, datapoint):
  global data
  #return data[dataname].setdefault(id, data[dataname + "_default"]).setdefault(datapoint, data[dataname + "_default"][datapoint])
  if id not in data[dataname]:
    data[dataname][id] = data[dataname + "_default"]
  elif datapoint not in data[dataname][id]:
    data[dataname][id][datapoint] = data[dataname + "_default"][datapoint]
  return data[dataname][id][datapoint]

def setdata(dataname, id, datapoint, value):
  global data
  if id not in data[dataname]:
    data[dataname][id] = {}
  data[dataname][id][datapoint] = value

def getadmins(datapoint = "", *include):
  return [userid for userid in data["admin"] if not datapoint or userid in include or getdata("admin", userid, datapoint)]
#endregion
