import requests
import json
from bottle import route, run, template, view
from pprint import pprint
from time import sleep
import os

apikey = 'e428f726-3fbd-4831-9dcc-5bc5b278bf73'

def getChamps():
  champs = {}
  r = requests.get('https://global.api.pvp.net/api/lol/static-data/na/v1.2/champion?champData=all&api_key={0}'.format(apikey))
  data = json.loads(r.text)
  for row in data['keys']:
    champs[row] = data['keys'][row]
  return champs

def getItems():
  items = {}
  r = requests.get('https://global.api.pvp.net/api/lol/static-data/na/v1.2/item?itemListData=all&api_key={0}'.format(apikey))
  data = json.loads(r.text)
  data = data['data']
  for item_key in data:
    item = data[item_key]    
    items[item['id']] = item['name']
  return items
  

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

def getLastbuilds(pids, champ, region):
  builds = []
  for pid in pids:
    print('Ja foram {0} de um total de {1}'.format(pids.index(pid),len(pids)))
    go = False
    while not go:
      skip = False
      r = requests.get('https://br.api.pvp.net/api/lol/{0}/v2.2/matchhistory/{1}?championIds={2}&rankedQueues=RANKED_SOLO_5x5&api_key={3}'.format(region, pid, champ, apikey))
      if r.text.startswith('<html>'):
        sleep(1)
        print('zzz')
      else:
        data = json.loads(r.text)
        if data == {}:
          skip = True
          break
        if 'matches' in data:
          go = True
    
    if skip:
      continue
    try:
      if not data['matches'][0]['matchVersion'].startswith('5.16'): continue
      for match in data['matches']:
        player = match['participants'][0]
        stats = player['stats']
        build = (stats['item0'],stats['item1'],stats['item3'],stats['item4'],stats['item5'],stats['item6'])
        won = stats['winner']
        builds.append(build)
    except:
      print('Deu merda, debug:')
      pprint(data)

  return builds

def makeDb(region='br'):
  pids = getPids(region)
  for champ in [429]: #gChamps:
    builds = getLastbuilds(pids, champ, region)
    fn = os.path.join(os.path.dirname(__file__), '.'.join([str(champ),'json']))
    with open(fn, 'w') as f:
      for build in builds:
        f.write(','.join([str(x) for x in build]+['\n']))

def loadBuilds(champ, region):
  builds = []
  with open('.'.join([str(champ),'data']), 'r') as f:
    for line in f.readlines():
      line = line.strip('\n')
      if not line == '':
        builds.append([int(x) for x in line.split(',') if x != ''])
  return builds

@route('/')
@view('index')
def index():
  return dict(champs=gChamps)

@route('/show/<champ>/<region>')
@view('champ')
def show(champ='126', region='na'):
  pids = getPids(region)
  builds = loadBuilds(champ, region)
  return dict(builds=builds, items=gItems, champ=gChamps[champ])

gItems = getItems()
gChamps = getChamps()
#makeDb()
run(host='192.168.1.35', port='80')
