import requests
import json
from bottle import route, run, template, view, static_file, response, get, redirect
from pprint import pprint
from time import sleep
from collections import OrderedDict
import os
import operator

api_pool = ['e428f726-3fbd-4831-9dcc-5bc5b278bf73',
            '3376c62a-7907-40b5-acf2-ac0b2c2bbaee',
            '91468fbe-8912-498b-85db-6134b78b2f43',
            'b57a0cdb-9518-48a3-ab8e-39672da5a41a',
            'ad2d0cbd-3433-46a0-8b36-0fe270e41643',
            'd571dc1c-7cd1-4968-b6c2-40143fa86833']

apikey = api_pool[5]

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
    elif item == 3363:
      aux = 3342
    elif item == 3341:
      aux = 3364
    elif item in [3361, 3362]:
      aux = 3340
    elif item == 0:
      continue
    else:
      aux = item
    new_build.append(aux)
  return new_build

def getChamps():
  champs = {}
  files = os.listdir()
  for file in files:
    if file.endswith('.data'):
      cid = file.split('.')[0]
      champs[cid] = gChamps[cid]
  return champs

# This is exec on startup to fetch current champs from riot static data, doesn't count towards API req count
# Takes nothing, returns dict in form of: dict[id]: name, e.g dict[429]: kalista
def getAllChamps():
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
    fn = os.path.join(os.path.dirname(__file__), '.'.join([str(champ),'data']))
    if not os.path.isfile(fn):
      open(fn, 'a').close()
      builds = getLastbuilds(pids, champ, region)
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

def makeFinalbuild(builds):
  bootlist = [3047, 3158, 3117, 3020, 3009, 3006]
  boots = {3047:0, 3158:0, 3117:0, 3020:0, 3009:0, 3006:0}
  trinketlist = [3342, 3364, 3340]
  trinket = {3342:0, 3364:0, 3340:0}
  others = {}
  for build in builds:
    for item in build:
      if item in bootlist:
        boots[item] += 1
      elif item in trinketlist:
        trinket[item] += 1
      else:
        if item in others:
          others[item] += 1
        else:
          others[item] = 1
  final = []
  final.append(max(trinket, key=trinket.get))
  final.append(max(boots, key=boots.get))
  for i in range(5):
    final.append(max(others, key=others.get))
    del others[final[-1]]
  return final

@route('/')
@view('www/landing')  # this is index.tpl call
def index():
  return  # and this is what data is given to tpl file]

# default index page
@route('/main')
@view('www/main')  # this is index.tpl call
def index():
  return dict(champs=lChamps)  # and this is what data is given to tpl file

# same as above, but with changeable arguments for specific champ on a region
# almost sure its broken for any other args other than default, will fix
@route('/getbuild/:champ', method='GET')
def downloadBuild(champ):
  if int(champ) == 0:
    redirect("/main")
    return 
  build = makeFinalbuild(loadBuilds(champ, 'br'))
  fn = os.path.join(os.path.dirname(__file__), '.'.join([str(champ),'json']))
  jdata = OrderedDict()
  jdata['title'] = 'Challenjour Builds'
  jdata['type'] = 'custom'
  jdata['map'] = 'any'
  jdata['mode'] = 'any'
  jdata['priority'] = False
  jdata['sortrank'] = 0
  itemdata = []
  for item in build:
    itemdata.append({'id': item, 'count': 1})
  data = {'type': 'BEST BUILD BR',
          'recMath': False,
          'minSummonerLevel': -1,
          'maxSummonerLevel': -1,
          'showIfSummonerSpell': "",
          'hideIfSummonerSpell': "",
          'items': itemdata,
          }
  block = [data]
  jdata['blocks'] = block
  
  dump = json.dumps(jdata, ensure_ascii=False)
  with open(fn, 'w') as f:
    f.write(dump)
  return static_file(fn, root='./', download=fn)

@route('/<style>')
def stylesheets(style):
    return static_file(style, root='./www/')

@route('/bkg/<img>')
def background(img):
    return static_file(img, root='./www/bkg')


# startup here
# these 2 lines below must be kept
gItems = getItems()
gChamps = getAllChamps()
lChamps = getChamps()

# chose 1 of 2 lines
# first is fetching data mode
# second is actually app mode
#makeDb()
run(host='192.168.0.12', port='8080')
