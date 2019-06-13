


# IMPORTANT IMPORTANT IMPORTANT IMPORTANT IMPORTANT IMPORTANT IMPORTANT



# Chaque fois que vous modifiez le fichier et que vous le téléchargez sur GitHub,
# veuillez changer le sous-index de version (par exemple de v1.0 à v1.1).
# Lorsque vous avez une version qui fonctionne et que vous considérez bonne,
# augmentez le numéro de version (de v1.1 à v2.0).



# IMPORTANT IMPORTANT IMPORTANT IMPORTANT IMPORTANT IMPORTANT IMPORTANT







################### Importation des modules ###################################

# Modules pour html
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs, unquote
import json

# Modules pour les graphs
import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as mdates

# Module pour la base des données
import sqlite3



################## Définition des parametres d'une station ####################

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



############## Initialisation avec la base des données ########################

# Récupération de la liste des stations météo de la BDD
conn = sqlite3.connect('Temperatures.sqlite')
c = conn.cursor()
station_list=[]
c.execute("SELECT * FROM 'stations-meteo'")
r = c.fetchall()
#current_station=0
for a in r:
    station_list.append(station(a[0],a[1],a[2],a[3],a[4]))

############## Déclaration de la liste des régions (Variable globale) #########  
    
stations_selectionnes=[]


############## Définition du nouveau handler ##################################

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    # sous-répertoire racine des documents statiques
    static_dir = '/client'
    current_station=0
    
    # On surcharge la méthode qui traite les requêtes GET
    def do_GET(self):
        # On récupère les étapes du chemin d'accès
        self.init_params()
       
        # le chemin d'accès commence par /stations
        if self.path_info[0] == 'stations':
            self.send_stations()
          
        # le chemin d'accès commence par /temperature
        elif self.path_info[0] == 'temperature':
            self.send_temperature()
        
        # le chemin d'accès commence par /detail
        elif self.path_info[0] == 'detail':
            self.send_detail()
          
        # ou pas...
        else:
            self.send_static()



########## On surcharge la méthode qui traite les requêtes HEAD ###############
  
    def do_HEAD(self):
        self.send_static()



############# On envoie le document statique demandé ##########################
  
    def send_static(self):

        # on modifie le chemin d'accès en insérant un répertoire préfixe
        self.path = self.static_dir + self.path
    
        # on appelle la méthode parent (do_GET ou do_HEAD)
        # à partir du verbe HTTP (GET ou HEAD)
        if (self.command=='HEAD'):
            http.server.SimpleHTTPRequestHandler.do_HEAD(self)
        else:
            http.server.SimpleHTTPRequestHandler.do_GET(self)



######## On analyse la requête pour initialiser nos paramètres ################
  
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
    


##### On génère et on renvoie la liste des stations et leur coordonnées #######
  
    def send_stations(self): # la fonction pour envoyer les latitudes et lontitudes.
        headers = [('Content-Type','application/json')];
        body = json.dumps([{'nom':i.get_nom(), 'lat':i.get_lat_vrai(), 'lon': i.get_lon_vrai()} for i in station_list])
        i=station_list[0]
        self.send(body,headers)



############## On génère et on renvoie un graphique de temperature ############
  
    def send_temperature(self): # pour afficher les informations d'une station
        # Connexion à la BDD
        conn = sqlite3.connect('Temperatures.sqlite')
        c = conn.cursor()
        
        for s in station_list:
          if s.get_nom()==self.path_info[1]:
            station_temp=s
        
        # Intervalle de temps considéré
        deb,fin = self.path_info[3],self.path_info[4]
        
        # Passage du format AAAA-MM-JJ à AAAAMMJJ
        deb=deb[:4]+deb[5:7]+deb[8:10]
        fin=fin[:4]+fin[5:7]+fin[8:10]
        pas = self.path_info[5]
        
        if self.path_info[2]=='Moyenne':  sheet=  'TG_1978-2018'
        elif self.path_info[2]=='Maximale': sheet= 'TX_1978-2018'
        elif self.path_info[2]=='Minimale': sheet=  'TN_1978-2018'
        
		#Creation du schema du ficher qu'on veut
        fichier = 'courbes/temperature_'+self.path_info[1]+self.path_info[2] +deb+fin+pas+'.png'
		
		# On voit si l'entrée est déjà dans le cache
        c.execute("SELECT * FROM cache WHERE station='{}' AND type='{}' AND debut='{}' AND fin='{}' AND pas='{}'".format(self.path_info[1],self.path_info[2],deb,fin,pas))
        r = c.fetchall()
	
        # Selon la reponse que cette requete, on crée la courbe ou on la cherche
        # La courbe n'est pas dans le cache
        if not r:
			
            # On ajoute la ligne a la base des données
            c.execute("INSERT INTO cache VALUES(?,?,?,?,?)",[self.path_info[1],self.path_info[2],deb,fin,pas])
            conn.commit()
            
            # On crée la courbe
            
            # Requête SQL
            c.execute("SELECT * FROM '{}' WHERE Date > {} AND Date < {} AND STAID={} ORDER BY Date".format(sheet,deb,fin,station_temp.get_num()))
            r = c.fetchall()
			# prise en compte du pas, intervalle de temps minimale considéré
            r_pas = [r[i] for i in range(0,len(r),int(pas))]
            
            # recupération de la date (colonne 2) et transformation dans le format de pyplot
            x = [mdates.date2num(dt.date(int(str(a[2])[:4]),int(str(a[2])[4:6]),int(str(a[2])[6:8]))) for a in r_pas]
            # récupération de les températures (colonne 4)
            y = [float(a[3])/10 for a in r_pas]
            
            # configuration du tracé
            fig = plt.figure(figsize=(18,6))
            ax = fig.add_subplot(111)
            ax.set_ylim(bottom=-10,top=40)
            ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
            
            # Configuration de l'axe des absisses en fonction de la longueur de l'intervalle
            if int(fin[:4])-int(deb[:4]) < 3:
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%Y'))
                ax.xaxis.set_minor_locator(mdates.MonthLocator())
            else:
                ax.xaxis.set_major_locator(mdates.YearLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                ax.xaxis.set_minor_locator(mdates.YearLocator())
                
            ax.xaxis.set_tick_params(labelsize=12)
            ax.xaxis.set_label_text("Années")
            ax.yaxis.set_label_text("Température °C")
            
            # tracé de la courbe
            plt.plot(x,y,linewidth=1, linestyle='-', marker='o', color='blue', label=station_temp.get_nom())
            fig.autofmt_xdate()
            ax.grid(True)
            
            # légendes
            plt.legend(loc='lower left')
            plt.title('Température {} de {} en ºC'.format(self.path_info[2],self.path_info[1]),fontsize=16)
            
            
            # génération des courbes dans un fichier PNG
            plt.savefig('client/{}'.format(fichier))
        
        body = json.dumps({
                'title': 'Température {} de'.format(self.path_info[2])+self.path_info[1], \
                'img': '/'+fichier \
                 });
        
        # Envoie de la requête
        headers = [('Content-Type','application/json')];
        self.send(body,headers)



############### On envoie les details de une station ##########################
  
    def send_detail(self):
        current_station=self.path_info[1]
        if current_station not in stations_selectionnes:
            stations_selectionnes.append(current_station)
        for i in station_list:
            if(self.path_info[1] == i.get_nom()):
                station = i
        body = json.dumps({'nom':station.get_nom(),\
                           'num': station.get_num(), \
                           'lat': station.get_lat(), \
                           'lon': station.get_lon(), \
                           'high' : station.get_high(), \
                           'station_select': stations_selectionnes, \
                           });
        
        headers = [('Content-Type','application/json')];
    
        self.send(body,headers)



############ On envoie les entêtes et le corps fourni #########################
    
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


 
############# Instanciation et lancement du serveur ###########################

httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()