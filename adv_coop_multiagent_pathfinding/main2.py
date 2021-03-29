# -*- coding: utf-8 -*-

# Nicolas, 2021-03-05
from __future__ import absolute_import, print_function, unicode_literals

import random 
import numpy as np
import sys
from itertools import chain


import pygame

from pySpriteWorld.gameclass import Game,check_init_game_done
from pySpriteWorld.spritebuilder import SpriteBuilder
from pySpriteWorld.players import Player
from pySpriteWorld.sprite import MovingSprite
from pySpriteWorld.ontology import Ontology
import pySpriteWorld.glo

from search.grid2D import ProblemeGrid2D
from search import probleme




# ---- ---- ---- ---- ---- ----
# ---- Misc                ----
# ---- ---- ---- ---- ---- ----




# ---- ---- ---- ---- ---- ----
# ---- Main                ----
# ---- ---- ---- ---- ---- ----

game = Game()

def init(_boardname=None):
    global player,game
    name = _boardname if _boardname is not None else 'demoMap'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 5  # frames per second
    game.mainiteration()
    player = game.player
    
def main():

    #for arg in sys.argv:
    iterations = 100 # default
    if len(sys.argv) == 2:
        iterations = int(sys.argv[1])
    print ("Iterations: ")
    print (iterations)

    init()
    

    
    #-------------------------------
    # Initialisation
    #-------------------------------
    
    nbLignes = game.spriteBuilder.rowsize
    nbCols = game.spriteBuilder.colsize
       
    print("lignes", nbLignes)
    print("colonnes", nbCols)
    
    
    players = [o for o in game.layers['joueur']]
    nbPlayers = len(players)
    score = [0]*nbPlayers
    
       
           
    # on localise tous les états initiaux (loc du joueur)
    # positions initiales des joueurs
    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    print ("Init states:", initStates)
    
    # on localise tous les objets ramassables
    # sur le layer ramassable
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    print ("Goal states:", goalStates)
        
    # on localise tous les murs
    # sur le layer obstacle
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]
    print ("Wall states:", wallStates)
    
    def legal_position(row,col):
        # une position legale est dans la carte et pas sur un mur
        return ((row,col) not in wallStates) and row>=0 and row<nbLignes and col>=0 and col<nbCols
        
    #-------------------------------
    # Attributaion aleatoire des fioles 
    #-------------------------------
    
    objectifs = goalStates
    random.shuffle(objectifs)
    print("Objectif joueur 0", objectifs[0])
    print("Objectif joueur 1", objectifs[1])

    players = [o for o in game.layers['joueur']]
    nbPlayers = len(players)
    # On veut un nombre de joueurs pairs (afin de réaliser des équipes d'effectifs égaux)
    if (nbPlayers % 2) :
        print("Le nombre de joueurs n'est pas pair (impossible de créer des équipes d'effectifs égaux). Fermeture du jeu.")
        pygame.quit()
        exit()
    score = [0]*nbPlayers
           
    # on localise tous les états initiaux (loc du joueur)
    # positions initiales des joueurs
    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    print ("Init states:", initStates)
    
    # on localise tous les objets ramassables
    # sur le layer ramassable
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    print ("Goal states:", goalStates)
        
    # on localise tous les murs
    # sur le layer obstacle
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]
    print ("Wall states:", wallStates)
    
    def legal_position(row,col):
        # une position legale est dans la carte et pas sur un mur
        return ((row,col) not in wallStates) and row>=0 and row<nbLignes and col>=0 and col<nbCols
        
    #-------------------------------
    # Attributaion aleatoire des fioles 
    #-------------------------------
    
    objectifs = goalStates
    random.shuffle(objectifs)
    for j in range(nbPlayers) :
        print("Objectif joueur ", j, ":", objectifs[0])

    #-------------------------------
    # Création de la liste des chemins, des problemes, de choix d'algo et de temps de parcours
    #-------------------------------

    liste_prob = list() # Permet de regrouper tout les problemes par joueur
    liste_path = list() # Permet de regrouper tout les chemins par joueur
    liste_temps = list() # Permet de regrouper tout les temps par joueur
    liste_algo = list() # Permet de regrouper les choix des joueurs en termes d'algo de recherche

    #-------------------------------
    # Attribution des algos de recherche
    #-------------------------------

    # Indice d'algo de recherche :
    # 0 : A*
    # 1 : GreedyBestFirst
    # 2 : RandomBestFirst
    # 3 : Coop_astar
    list_algo = [3, 3, 3, 3, 3, 3] # Hypothese : len(list_algo) == nbPlayers

    # Vérification des valeurs dans list_algo
    for i in range(len(list_algo)) :
        if ((list_algo[i] < 0) or (list_algo[i] > 3)) : # Une valeur non-existante d'algo a été attribuée
            list_algo[i] = random.randint(0, 3) # On donne un algo aléatoire au joueur j


    if (len(list_algo) != nbPlayers) :
        # Dans le cas où le nombre d'algos par joueur ne correspond pas au nombre de joueurs
        print("Erreur - Le nombre d'algos dans list_algo ne correspond pas avec le nombre de joueurs. Attribution aléatoire des algos pour tout les joueurs.")
        list_algo = []

        # On attribue aléatoirement des algos aux joueurs
        for i in range(nbPlayers) :
            list_algo.append(random.randint(0, 3))

    #-------------------------------
    # Calculs des chemins pour les joueurs
    #-------------------------------

    dico = dict()
    for j in range(nbPlayers) :
        g =np.ones((nbLignes,nbCols),dtype=bool)  # par defaut la matrice comprend des True 

        for w in wallStates:            # putting False for walls
            g[w]=False

        liste_prob.append(ProblemeGrid2D(initStates[j],objectifs[j],g,'manhattan')) # On ajoute le probleme à la liste des problèmes

        # On crée path en avance :
        path = list()

        # On crée le path vers l'objectif avec l'algorithme de notre choix (choix effectue dans liste_algo plus haut)
        if (list_algo[j] == 0) :
            path = probleme.astar(liste_prob[j])
        if (list_algo[j] == 1) :
            path = probleme.greedyBestFirst(liste_prob[j])
        if (list_algo[j] == 2) :
            path = probleme.randomBestFirst(liste_prob[j])
        if (list_algo[j] == 3) :
            path = probleme.coop_astar(liste_prob[j],dico)


        # On ajoute le path à la liste des paths
        liste_path.append(path)
        print ("Joueur", j, "Chemin trouvé:", liste_path[j])

        # On initialise le temps à 0
        liste_temps.append(0)
    #-------------------------------
    # Carte demo 
    # 2 joueurs 
    # Joueur 0: A*
    # Joueur 1: random walker
    #-------------------------------
    
    #-------------------------------
    # calcul A* pour le joueur 1
    #-------------------------------
    

    
    #-------------------------------
    # Boucle principale de déplacements 
    #-------------------------------
    
            
    posPlayers = initStates

    for i in range(iterations):
        
        # on fait bouger chaque joueur séquentiellement
        
        # Joeur 0: suit son chemin trouve avec A* 
        
        row,col = path[i]
        posPlayers[0]=(row,col)
        players[0].set_rowcol(row,col)
        print ("pos 0:", row,col)
        if (row,col) == objectifs[0]:
            score[0]+=1
            print("le joueur 0 a atteint son but!")
            break
        
        # Joueur 1: fait du random walk
        
        row,col = posPlayers[1]

        while True: # tant que pas legal on retire une position
            x_inc,y_inc = random.choice([(0,1),(0,-1),(1,0),(-1,0)])
            next_row = row+x_inc
            next_col = col+y_inc
            if legal_position(next_row,next_col):
                break
        players[1].set_rowcol(next_row,next_col)
        print ("pos 1:", next_row,next_col)
    
        col=next_col
        row=next_row
        posPlayers[1]=(row,col)
            
        if (row,col) == objectifs[1]:
            score[1]+=1
            print("le joueur 1 a atteint son but!")
            break
            
            
        
        # on passe a l'iteration suivante du jeu
        game.mainiteration()

                
        
            
    
    print ("scores:", score)
    pygame.quit()
    
    
    
    
    #-------------------------------
    
        
        
    
    
        
   

 
    
   

if __name__ == '__main__':
    main()