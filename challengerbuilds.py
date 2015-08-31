import requests
import json
from bottle import route, run, template, view
from pprint import pprint
from time import sleep
import os

apikey = 'e428f726-3fbd-4831-9dcc-5bc5b278bf73'
apikey2 = '8064ce2e-adfd-4655-b0f8-cba6eb0408d3'

# take an build and returns without boots enchantments
def removeEnchant(build):
  new_build = []
  ninja_e = [1315, 1316, 1338, 1317, 1318, 1319] #3047 Ninja
  ionia_e = [1330, 1341, 1331, 1332, 1333, 1334] #3158 Ionian
  mobil_e = [1329, 1328, 1325, 1327, 1326, 1340] #3117 Mobility
  sorce_e = [1314, 1313, 1312, 1311, 1310, 1337] #3020 Sorcerer
  swift_e = [1307, 1306, 1309, 1308, 1305, 1336] #3009 Swiftness
  grave_e = [1301, 1300, 1303, 1302, 1304, 1335] #3006 Greaves
  for item in build:
    if item in ninja_e:
      aux = 3047
    elif item in ionia_e:
      aux = 3158
    elif item in mobil_e:
      aux = 3117
    elif item in sorce_e:
      aux = 3020
    elif item in swift_e:
      aux = 3009
    elif item in grave_e:
      aux = 3006
    else:
      aux = item
    new_build.append(aux)
  return new_build

# This is exec on startup to fetch current champs from riot static data, doesn't count towards API req count
# Takes nothing, returns dict in form of: dict[id]: name, e.g dict[429]: kalista
def getChamps():
  champs = {}
  r = requests.get('https://global.api.pvp.net/api/lol/static-data/na/v1.2/champion?champData=all&api_key={0}'.format(apikey))
  data = json.loads(r.text)
  for row in data['keys']:
    champs[row] = data['keys'][row]
  return champs


# This is exec on startup to fetch current items from riot static data, doesn't count towards API req count
# Takes nothing, returns dict in form of: dict[id]: name, e.g dict[3125]: void staff
def getItems():
  items = {}
  r = requests.get('https://global.api.pvp.net/api/lol/static-data/na/v1.2/item?itemListData=all&api_key={0}'.format(apikey))
  data = json.loads(r.text)
  data = data['data']
  for item_key in data:
    item = data[item_key]    
    items[item['id']] = item['name']
  return items
  
# This is executed before starting to fecthing builds, it gets all Summoner IDS
# from Challenge and Master league from a region
# Takes region, return list of IDS, e.g list = [23466, 1008493, 48940]
def getPids(region):
  r = requests.get('https://br.api.pvp.net/api/lol/{0}/v2.5/league/challenger?type=RANKED_SOLO_5x5&api_key={1}'.format(region, apikey))
  data = json.loads(r.text)
  pids = []
  for player in data['entries']:
    pids.append(player['playerOrTeamId'])
    
  r = requests.get('https://br.api.pvp.net/api/lol/{0}/v2.5/league/master?type=RANKED_SOLO_5x5&api_key={1}'.format(region, apikey))
  data = json.loads(r.text)
  for player in data['entries']:
    pids.append(player['playerOrTeamId'])
  return pids

# Fetch builds from the latest 15 games on current patch(5.16)
# from all summoners on a list pids from a region, by a specific champ
# takes SummonerIDS(pids), champID (champ), region. returns list of lists of builds by id of items
# e.g: [[1234,6549,1234,9875], [985470,3652,49875]]
def getLastbuilds(pids, champ, region):
  builds = []
  for pid in pids:
    print('{0} done. {1} to go'.format(pids.index(pid),len(pids))) #tracking progress
    go = False
    while not go:
      skip = False
      r = requests.get('https://br.api.pvp.net/api/lol/{0}/v2.2/matchhistory/{1}?championIds={2}&rankedQueues=RANKED_SOLO_5x5&api_key={3}'.format(region, pid, champ, apikey))
      if r.text.startswith('<html>'):  # if <html is returned is a timeout error or smth weird
        sleep(1)
        print('zzz')
      else:
        data = json.loads(r.text)
        if data == {}: #this happens when the player doesnt played the champion on ranked solo
          skip = True # so we skip to next person
          break
        if 'matches' in data: #if the key matches exits, it's a regular data from the player
          go = True           #else it is a code responde from riot 429, or smth, we just try again
    
    if skip:
      continue
    try:
      if not data['matches'][0]['matchVersion'].startswith('5.16'): continue
      # check if the first match is form this patch, otherwise drop this data
      # matches are fetched from most recent -> most older
      for match in data['matches']:
        player = match['participants'][0]
        stats = player['stats']
        build = (stats['item0'],stats['item1'],stats['item3'],stats['item4'],stats['item5'],stats['item6'])
        won = stats['winner']
        builds.append(build)
    except:
      print('Err')  #shouldn't go here, never ever

  return builds

#takes a region, and fetch data for all champs, should't be executed with normal webserver
#because it consumes requests quota pretty fast
# on finish, it writes "idchamp.data" on app folder
# 429.data it's kalista builds for e.g
def makeDb(region='br'):
  pids = getPids(region)
  for champ in gChamps:
    print("Doing ",  gChamps[champ])
    builds = getLastbuilds(pids, champ, region)
    fn = os.path.join(os.path.dirname(__file__), '.'.join([str(champ),'data']))
    with open(fn, 'w') as f:
      for build in builds:
        f.write(','.join([str(x) for x in build]+['\n']))


# get data for a specific champion, for now region is ignored
def loadBuilds(champ, region):
  builds = []
  with open('.'.join([str(champ),'data']), 'r') as f:
    for line in f.readlines():
      line = line.strip('\n')
      if not line == '':
        builds.append(removeEnchant([int(x) for x in line.split(',') if x != '']))
  return builds

# default index page
@route('/')
@view('index')  # this is index.tpl call
def index():
  return dict(champs=gChamps)  # and this is what data is given to tpl file


#same as above, but with changeable arguments for specific champ on a region
# almost sure its broken for any other args other than default, will fix
@route('/show/<champ>/<region>')
@view('champ')
def show(champ='126', region='na'):
  pids = getPids(region)
  builds = loadBuilds(champ, region)
  return dict(builds=builds, items=gItems, champ=gChamps[champ])


# startup here
# these 2 lines below must be kept
gItems = getItems()
print(gItems)
#gChamps = getChamps()

# chose 1 of 2 lines
# first is fetching data mode
# second is actually app mode
#makeDb()
#run(host='127.0.0.1', port='80')
