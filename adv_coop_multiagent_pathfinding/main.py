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
    name = 'exAdvCoopMap'
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
    list_algo = [0, 0, 0, 0, 0, 0] # Hypothese : len(list_algo) == nbPlayers

    # Vérification des valeurs dans list_algo
    for i in range(len(list_algo)) :
        if ((list_algo[i] < 0) or (list_algo[i] > 2)) : # Une valeur non-existante d'algo a été attribuée
            list_algo[i] = random.randint(0, 2) # On donne un algo aléatoire au joueur j


    if (len(list_algo) != nbPlayers) :
        # Dans le cas où le nombre d'algos par joueur ne correspond pas au nombre de joueurs
        print("Erreur - Le nombre d'algos dans list_algo ne correspond pas avec le nombre de joueurs. Attribution aléatoire des algos pour tout les joueurs.")
        list_algo = []

        # On attribue aléatoirement des algos aux joueurs
        for i in range(nbPlayers) :
            list_algo.append(random.randint(0, 2))

    #-------------------------------
    # Calculs des chemins pour les joueurs
    #-------------------------------

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

        # On ajoute le path à la liste des paths
        liste_path.append(path)
        print ("Joueur", j, "Chemin trouvé:", liste_path[j])

        # On initialise le temps à 0
        liste_temps.append(0)

    #-------------------------------
    # Boucle principale de déplacements 
    #-------------------------------
    
    #-------------------------------
    # Déplacements sans random
    #-------------------------------

    posPlayers = initStates
    it = 0

    # On boucle tant que les joueurs ne sont tous pas arrivés à leur objectif
    while ((sum(score) != nbPlayers) and (it < iterations)) :

        for j in range(nbPlayers) :

            # On initialise row,col à init du probleme
            row,col = liste_prob[j].init

            # On vérifie si le joueur n'a pas terminé son chemin
            if (len(liste_path[j]) != 0) : 

                # Gestion de la collision avec d'autres joueurs
                for k in range(nbPlayers) :
                    if (k != j) : # On ne veut pas comparer un joueur avec lui-meme
                        if (len(liste_path[k]) != 0) : # On vérifie si le joueur comparé est toujours en déplacement
                            if (liste_path[k][0] == liste_path[j][0]) : # On vérifie qu'un autre joueur ne vas pas se déplacer sur la case où le joueur va se déplacer
                                
                                # Il y a collision entre agents
                                print("Collisions entre les joueurs", j, "et", k, ". Recalcul du chemin pour le joueur ", j, ".")

                                # On ajoute la position de l'agent rencontre comme mur temporairement
                                l,c = liste_path[k][0]
                                liste_prob[j].grid[l][c] = False

                                # On recalcule le path vers l'objectif avec l'algorithme de notre choix (choix effectue dans liste_algo plus haut)
                                if (list_algo[j] == 0) :
                                    liste_path[j] = probleme.astar(liste_prob[j]) # Pour parcourir en A*
                                if (list_algo[j] == 1) :
                                    liste_path[j] = probleme.greedyBestFirst(liste_prob[j]) # Pour parcourir en GreedyBestFirst
                                if (list_algo[j] == 2) :
                                    liste_path[j] = probleme.randomBestFirst(liste_prob[j]) # Pour parcourir en RandomBestFirst
                                print(liste_path[j])

                                # On retire la position de l'agent rencontre comme mur
                                liste_prob[j].grid[l][c] = True

                            """
                            # Cette vérification permet d'assurer encore plus qu'il n y aura pas de collisions
                            if (liste_prob[k].init == liste_path[j][0]) : # On vérifie que la case sur laquelle on souhaite se déplacer n'est pas déjà occupée par un joueur (avec init)
                                
                                # Il y a collision entre agents
                                print("Collisions entre les joueurs", j, "et", k, ". Recalcul du chemin pour le joueur ", j, ".")

                                # On ajoute la position de l'agent rencontre comme mur temporairement
                                l,c = liste_path[k][0]
                                liste_prob[j].grid[l][c] = False

                                # On recalcule le path vers l'objectif avec l'algorithme de notre choix (choix effectue dans liste_algo plus haut)
                                if (list_algo[j] == 0) :
                                    liste_path[j] = probleme.astar(liste_prob[j]) # Pour parcourir en A*
                                if (list_algo[j] == 1) :
                                    liste_path[j] = probleme.greedyBestFirst(liste_prob[j]) # Pour parcourir en GreedyBestFirst
                                if (list_algo[j] == 2) :
                                    liste_path[j] = probleme.randomBestFirst(liste_prob[j]) # Pour parcourir en RandomBestFirst
                                print(liste_path[j])

                                # On retire la position de l'agent rencontre comme mur
                                liste_prob[j].grid[l][c] = True
                            """

                        elif (posPlayers[k] == liste_path[j][0]) : # Le joueur comparé est statique sur une case 
                                
                            # Il y a collision entre agents
                            print("Collisions entre les joueurs", j, "et", k, ". Recalcul du chemin pour le joueur ", j, ".")

                            # On ajoute la position de l'agent rencontre comme mur temporairement
                            l,c = posPlayers[k]
                            liste_prob[j].grid[l][c] = False

                            # On recalcule le path vers l'objectif avec l'algorithme de notre choix (choix effectue dans liste_algo plus haut)
                            if (list_algo[j] == 0) :
                                liste_path[j] = probleme.astar(liste_prob[j]) # Pour parcourir en A*
                            if (list_algo[j] == 1) :
                                liste_path[j] = probleme.greedyBestFirst(liste_prob[j]) # Pour parcourir en GreedyBestFirst
                            if (list_algo[j] == 2) :
                                liste_path[j] = probleme.randomBestFirst(liste_prob[j]) # Pour parcourir en RandomBestFirst
                            print(liste_path[j])

                            # On retire la position de l'agent rencontre comme mur
                            liste_prob[j].grid[l][c] = True
                            

                # Déplacement du joueur
                row,col = liste_path[j][0]
                posPlayers[j]=(row,col)
                players[j].set_rowcol(row,col) # On déplace le joueur

                liste_temps[j] = liste_temps[j] + 1 # On incrémente de 1 le temps de parcours du joueur

                liste_prob[j].init = (row,col) # On modifie l'état initial du probleme
                liste_path[j] = liste_path[j][1::] # On supprime le premier élément de la liste

                # Dans le cas où le chemin est vide, on ajoute l'état final du joueur comme mur dans les problèmes de tout les joueurs
                if (len(liste_path[j]) == 0) :
                    for i in range(nbPlayers) :
                        liste_prob[i].grid[row][col] = False
            
            print ("Tour de jeu", it, "- Position joueur", j, ":", row,col)

            if (score[j] == 0) :
                if (row,col) == objectifs[j]:
                    score[j]+=1
                    print("Le joueur", j, " a atteint son but!")

        # On passe a l'iteration suivante du jeu
        game.mainiteration()
        it = it + 1
    
    print ("Scores:", score)
    print("Temps de parcours:", liste_temps)
    pygame.quit()
    
       
    #-------------------------------


if __name__ == '__main__':
    main()
    


