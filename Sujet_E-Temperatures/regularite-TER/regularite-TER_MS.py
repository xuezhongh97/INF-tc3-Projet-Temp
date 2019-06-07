# regularite-TER.py
# Correpond au corrigé du dernier exercice du TD3+4 (TD3-s7.py)

import http.server
import socketserver
from urllib.parse import urlparse, parse_qs, unquote
import json

import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as pltd

import sqlite3

class station:
    '''Classe caractérisant une station météo'''
    
    def __init__(self,num,nom,lat,lon,high):
        self.num=num  #nombre
        self.nom=nom  #nom
        self.lat=lat  #latitude
        self.lon=lon  #longtitude
        self.high=high#altitude
        
    def get_num(self):
        return self.num

    def get_nom(self):
        return self.nom

    def get_lat(self): #valeur sous form "+***:**:** "
        return self.lat

    def get_lon(self):
        return self.lon

    def get_high(self):
        return self.high

    def get_lat_vrai(self): #valeur en nombre
        lantemp=self.lat.split(":")
        return int(lantemp[0])+int(lantemp[1])/60+int(lantemp[2])/6000

    def get_lon_vrai(self):
        lontemp=self.lon.split(":")
        return int(lontemp[0])+int(lontemp[1])/60+int(lontemp[2])/6000

# Récupération de la liste des stations météo de la BDD
conn = sqlite3.connect('Temperatures.sqlite')
c = conn.cursor()
station_list=[]
c = conn.cursor()
c.execute("SELECT * FROM 'stations-meteo'")
r = c.fetchall()
#current_region=0
for a in r:
    station_list.append(station(a[0],a[1],a[2],a[3],a[4]))

#
# Définition du nouveau handler
#

class RequestHandler(http.server.SimpleHTTPRequestHandler):
  # sous-répertoire racine des documents statiques
  static_dir = '/client'
  current_region=0
  # On surcharge la méthode qui traite les requêtes GET
  #
  def do_GET(self):

    # On récupère les étapes du chemin d'accès
    self.init_params()

    # le chemin d'accès commence par /time
    if self.path_info[0] == 'time':
      self.send_time()
   
     # le chemin d'accès commence par /regions
    elif self.path_info[0] == 'regions':
      self.send_regions()
      
    # le chemin d'accès commence par /ponctualite2020
    elif self.path_info[0] == 'ponctualite':
      self.send_ponctualite()
      
    elif self.path_info[0] == 'detail':
      self.send_detail()
      
    # ou pas...
    else:
      self.send_static()

  #
  # On surcharge la méthode qui traite les requêtes HEAD
  #
  def do_HEAD(self):
    self.send_static()

  #
  # On envoie le document statique demandé
  #
  def send_static(self):

    # on modifie le chemin d'accès en insérant un répertoire préfixe
    self.path = self.static_dir + self.path

    # on appelle la méthode parent (do_GET ou do_HEAD)
    # à partir du verbe HTTP (GET ou HEAD)
    if (self.command=='HEAD'):
        http.server.SimpleHTTPRequestHandler.do_HEAD(self)
    else:
        http.server.SimpleHTTPRequestHandler.do_GET(self)
  
  #     
  # on analyse la requête pour initialiser nos paramètres
  #
  def init_params(self):
    # analyse de l'adresse
    info = urlparse(self.path)
    self.path_info = [unquote(v) for v in info.path.split('/')[1:]]  # info.path.split('/')[1:]
    self.query_string = info.query
    self.params = parse_qs(info.query)

    # récupération du corps
    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' : 
        self.params = parse_qs(self.body)
    else:
      self.body = ''
   
    # traces
    print('info_path =',self.path_info)
    print('body =',length,ctype,self.body)
    print('params =', self.params)
    
  #
  # On envoie un document avec l'heure
  #
  def send_time(self):
    # on récupère l'heure
    time = self.date_time_string()

    # on génère un document au format html
    body = '<!doctype html>' + \
           '<meta charset="utf-8">' + \
           '<title>l\'heure</title>' + \
           '<div>Voici l\'heure du serveur :</div>' + \
           '<pre>{}</pre>'.format(time)

    # pour prévenir qu'il s'agit d'une ressource au format html
    headers = [('Content-Type','text/html;charset=utf-8')]

    # on envoie
    self.send(body,headers)

  #
  # On génère et on renvoie la liste des régions et leur coordonnées (version TD3)
  #
  def send_regions(self): # la fonction pour envoyer les latitudes et lontitudes.
    headers = [('Content-Type','application/json')];
    body = json.dumps([{'nom':i.get_nom(), 'lat':i.get_lat_vrai(), 'lon': i.get_lon_vrai()} for i in station_list])
    i=station_list[0]
    self.send(body,headers)
  #
  # On génère et on renvoie un graphique de ponctualite (cf. TD1)
  #
  def send_ponctualite(self): # pour afficher les informations d'une station
    conn = sqlite3.connect('Temperatures.sqlite')
    c = conn.cursor()

    for i in station_list:
      if i.get_nom()==self.path_info[1]:
        station_temp=i
    
    deb,fin = self.path_info[3],self.path_info[4]
    # Passage du format AAAA-MM-JJ à AAAAMMJJ
    deb=deb[:4]+deb[5:7]+deb[8:10]
    fin=fin[:4]+fin[5:7]+fin[8:10]
    pas = self.path_info[5]
    
    # configuration du tracé
    fig1 = plt.figure(figsize=(18,6))
    ax = fig1.add_subplot(111)
    ax.set_ylim(bottom=-10,top=40)
    ax.grid(which='major', color='#888888', linestyle='-')
    ax.grid(which='minor',axis='x', color='#888888', linestyle=':')
    ax.xaxis.set_major_locator(pltd.YearLocator())
    ax.xaxis.set_minor_locator(pltd.MonthLocator())
    ax.xaxis.set_major_formatter(pltd.DateFormatter('%B %Y'))
    ax.xaxis.set_tick_params(labelsize=10)
    ax.xaxis.set_label_text("Date")
    ax.yaxis.set_label_text("ºC")
            
    if self.path_info[2]=='Moyenne':  sheet=  'TG_1978-2018'
    elif self.path_info[2]=='Maximale': sheet= 'TX_1978-2018'
    elif self.path_info[2]=='Minimale': sheet=  'TN_1978-2018'
    c.execute("SELECT * FROM '{}' WHERE Date > {} AND Date < {} AND STAID={} ORDER BY Date".format(sheet,deb,fin,station_temp.get_num()))
    r = c.fetchall()
    # prise en compte du pas, intervalle de temps minimale considéré
    r_pas = [r[i] for i in range(0,len(r),pas)]
    # recupération de la date (colonne 2) et transformation dans le format de pyplot
    x = [pltd.date2num(dt.date(int(str(a[2])[:4]),int(str(a[2])[4:6]),int(str(a[2])[6:8]))) for a in r_pas]
    # récupération de la régularité (colonne 8)
    y = [float(a[3])/10 for a in r_pas]
    # tracé de la courbe
    plt.plot(x,y,linewidth=1, linestyle='-', marker='o', color='blue', label=station_temp.get_nom())


    # légendes
    plt.legend(loc='lower left')
    plt.title('Température {} de {} en ºC'.format(self.path_info[2],self.path_info[1]),fontsize=16)

    # génération des courbes dans un fichier PNG
    fichier = 'courbes/ponctualite_'+self.path_info[1]+self.path_info[2] +'.png'
    plt.savefig('client/{}'.format(fichier))
    
    #html = '<img src="/{}?{}" alt="ponctualite {}" width="100%">'.format(fichier,self.date_time_string(),self.path)
    body = json.dumps({
            'title': 'Température {} de'.format(self.path_info[2])+self.path_info[1], \
            'img': '/'+fichier \
             });
    # on envoie
    headers = [('Content-Type','application/json')];
    print(1)
    self.send(body,headers)

  def send_detail(self):
    current_region=self.path_info[1]
    print("yes")
    print(current_region)
    for i in station_list:
      if(self.path_info[1] == i.get_nom()):
        station = i
    body = json.dumps({
      'nom':station.get_nom(),\
      'num': station.get_num(), \
      'lat': station.get_lat(), \
      'lon': station.get_lon(), \
      'high' : station.get_high(), \
      });
    
    headers = [('Content-Type','application/json')];

    self.send(body,headers)

  #
  # On envoie les entêtes et le corps fourni
  #
  def send(self,body,headers=[]):

    # on encode la chaine de caractères à envoyer
    encoded = bytes(body, 'UTF-8')

    # on envoie la ligne de statut
    self.send_response(200)

    # on envoie les lignes d'entête et la ligne vide
    [self.send_header(*t) for t in headers]
    self.send_header('Content-Length',int(len(encoded)))
    self.end_headers()

    # on envoie le corps de la réponse
    self.wfile.write(encoded)

 
#
# Instanciation et lancement du serveur
#
httpd = socketserver.TCPServer(("", 8082), RequestHandler)
httpd.serve_forever()
