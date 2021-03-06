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
    # name = 'Tunnel'
    # name = 'exAdvCoopMap'
    # name = 'bridgeMap'
    # name = 'TestMap'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 5 # frames per second
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
    # Initialisation des équipes et des scores d'équipe 
    #-------------------------------
    
    effectifEquipe = int(nbPlayers / 2) # Nombre de joueurs par équipe

    # On crée les équipes (remplissage)
    equipe1 = list() # Joueurs Nord
    equipe2 = list() # Joueurs Sud

    # Hypothèse :
    # Dans l'idéal, il faudrait qu'il y ait autant de joueurs des deux cotes de la carte afin de créer des équipes Nord et Sud d'effectif équivalent.

    # On attribue les joueurs aux équipes
    for i in range(nbPlayers) :
        if (i < effectifEquipe) :
            equipe1.append(players[i])
        else :
            equipe2.append(players[i])

    # On crée les scores des équipes
    score_eq1 = 0
    score_eq2 = 0

    #-------------------------------
    # Attributaion aleatoire des fioles 
    #-------------------------------
    
    objectifs = goalStates
    random.shuffle(objectifs)
    for j in range(nbPlayers) :
        print("Objectif joueur ", j, ":", objectifs[j])

    #-------------------------------
    # Création de la liste des chemins, des problemes, de choix d'algo et de temps de parcours
    #-------------------------------

    liste_prob = list() # Permet de regrouper tout les problemes par joueur
    liste_path = list() # Permet de regrouper tout les chemins par joueur
    liste_temps = list() # Permet de regrouper tout les temps par joueur
    liste_algo = list() # Permet de regrouper les choix des joueurs en termes d'algo de recherche

    #-------------------------------
    # Attribution des algos de recherche
    #
    # Indice d'algo de recherche :
    # 0 : A*
    # 1 : GreedyBestFirst
    # 2 : RandomBestFirst
    # 3 : CoopAstar
    # 4 : A* avec recalcul du chemin chaque N itérations
    # 5 : GreedyBestFirst avec recalcul du chemin chaque N itérations
    # 6 : RandomBestFirst avec recalcul du chemin chaque N itérations
    #-------------------------------

    # Compteur de stratégies
    nbStrats = 7

    list_algo = [5, 5] # Hypothese : len(list_algo) == nbPlayers
    liste_timer = [-1] * nbPlayers # Les timers sont utilisés dans certains algorithmes, ils seront initialisés plus tard
    timer = 5 # Nombre d'itérations avant le recalcul du chemin

    # Vérification des valeurs dans list_algo
    for i in range(len(list_algo)) :
        if ((list_algo[i] < 0) or (list_algo[i] >= nbStrats)) : # Une valeur non-existante d'algo a été attribuée
            list_algo[i] = random.randint(0, nbStrats - 1) # On donne un algo aléatoire au joueur j


    if (len(list_algo) != nbPlayers) :
        # Dans le cas où le nombre d'algos par joueur ne correspond pas au nombre de joueurs
        print("Erreur - Le nombre d'algos dans list_algo ne correspond pas avec le nombre de joueurs. Attribution aléatoire des algos pour tout les joueurs.")
        list_algo = []

        # On attribue aléatoirement des algos aux joueurs
        for i in range(nbPlayers) :
            list_algo.append(random.randint(0, nbStrats - 1))

    #-------------------------------
    # Calculs des chemins pour les joueurs
    #-------------------------------

    dicoEq1 = dict() # Dictionnaire Coop A* pour l'équipe 1
    dicoEq2 = dict() # Dictionnaire Coop A* pour l'équipe 2

    for j in range(nbPlayers) :
        g =np.ones((nbLignes,nbCols),dtype=bool)  # par defaut la matrice comprend des True 

        for w in wallStates: # putting False for walls
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
            if (players[j] in equipe1) :
                path = probleme.coop_astar(liste_prob[j],dicoEq1)
            else :
                path = probleme.coop_astar(liste_prob[j],dicoEq2)

        if (list_algo[j] == 4) :
            path = probleme.astar(liste_prob[j])
            list_algo[j] = 0 # On considère cette stratégie comme la stratégie AStar classique désormais
            liste_timer[j] = timer

        if (list_algo[j] == 5) :
            path = probleme.greedyBestFirst(liste_prob[j])
            list_algo[j] = 1 # On considère cette stratégie comme la stratégie GreedyBestFirst classique désormais
            liste_timer[j] = timer

        if (list_algo[j] == 6) :
            path = probleme.randomBestFirst(liste_prob[j])
            list_algo[j] = 2 # On considère cette stratégie comme la stratégie RandomBestFirst classique désormais
            liste_timer[j] = timer


        # On ajoute le path à la liste des paths
        liste_path.append(path)
        print ("Joueur", j, "Chemin trouvé:", liste_path[j])

        # On initialise le temps à 0
        liste_temps.append(0)

    #-------------------------------
    # Boucle principale de déplacements 
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
                dico = dict()
                # Gestion de la collision avec d'autres joueurs
                for k in range(nbPlayers) :
                    if (k != j) : # On ne veut pas comparer un joueur avec lui-meme
                        if (len(liste_path[k]) != 0) : # On vérifie si le joueur comparé est toujours en déplacement
                            if (liste_path[k][0] == liste_path[j][0]) : # On vérifie qu'un autre joueur ne vas pas se déplacer sur la case où le joueur va se déplacer
                                
                                # Il y a collision entre agents
                                print("Collisions entre les joueurs", j, "et", k, ". Recalcul du chemin pour le joueur ", j, ".")

                                # On vérifie si le joueur utilise un timer
                                if (liste_timer[j] != -1) :
                                    # On réinitialise le timer du joueur
                                    liste_timer[j] = timer

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
                                if (list_algo[j] == 3) :
                                    if (players[j] in equipe1) :
                                        liste_path[j] = probleme.coop_astar(liste_prob[j],dicoEq1)
                                    else :
                                        liste_path[j] = probleme.coop_astar(liste_prob[j],dicoEq2) # Pour parcourir en Coop A*
                                print(liste_path[j])

                                # On retire la position de l'agent rencontre comme mur
                                liste_prob[j].grid[l][c] = True

                            # Cette vérification permet d'assurer encore plus qu'il n y aura pas de collisions
                            if (liste_prob[k].init == liste_path[j][0]) : # On vérifie que la case sur laquelle on souhaite se déplacer n'est pas déjà occupée par un joueur (avec init)
                                
                                # Il y a collision entre agents
                                print("Collisions entre les joueurs", j, "et", k, ". Recalcul du chemin pour le joueur ", j, ".")

                                # On vérifie si le joueur utilise un timer
                                if (liste_timer[j] != -1) :
                                    # On réinitialise le timer du joueur
                                    liste_timer[j] = timer

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
                                if (list_algo[j] == 3) :
                                    if (players[j] in equipe1) :
                                        liste_path[j] = probleme.coop_astar(liste_prob[j],dicoEq1)
                                    else :
                                        liste_path[j] = probleme.coop_astar(liste_prob[j],dicoEq2) # Pour parcourir en Coop A*
                                print(liste_path[j])

                                # On retire la position de l'agent rencontre comme mur
                                liste_prob[j].grid[l][c] = True

                        elif (posPlayers[k] == liste_path[j][0]) : # Le joueur comparé est statique sur une case, comme un mur
                                
                            # Il y a collision entre agents
                            print("Collisions entre les joueurs", j, "et", k, ". Recalcul du chemin pour le joueur ", j, ".")

                            # On vérifie si le joueur utilise un timer
                            if (liste_timer[j] != -1) :
                                # On réinitialise le timer du joueur
                                liste_timer[j] = timer

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
                            if (list_algo[j] == 3) :
                                    if (players[j] in equipe1) :
                                        liste_path[j] = probleme.coop_astar(liste_prob[j],dicoEq1)
                                    else :
                                        liste_path[j] = probleme.coop_astar(liste_prob[j],dicoEq2) # Pour parcourir en Coop A*
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

                # On vérifie si le joueur utilise un timer
                if (liste_timer[j] != -1) :
                    # Le joueur possede un timer
                    liste_timer[j] = liste_timer[j] - 1
                    
                    # Dans le cas où le timer est à 0
                    if (liste_timer[j] == 0) :
                        # On doit recalculer le chemin en fonction de la stratégie utilisée
                        print("Timer arrivé à 0 pour le joueur", j, ".Recalcul de son itinéraire vers l'objectif.")
                        
                        # On recalcule le path vers l'objectif avec l'algorithme de notre choix (choix effectue dans liste_algo plus haut)
                        if (list_algo[j] == 0) :
                            liste_path[j] = probleme.astar(liste_prob[j]) # Pour parcourir en A*
                        if (list_algo[j] == 1) :
                            liste_path[j] = probleme.greedyBestFirst(liste_prob[j]) # Pour parcourir en GreedyBestFirst
                        if (list_algo[j] == 2) :
                            liste_path[j] = probleme.randomBestFirst(liste_prob[j]) # Pour parcourir en RandomBestFirst
                        if (list_algo[j] == 3) :
                            if (players[j] in equipe1) :
                                liste_path[j] = probleme.coop_astar(liste_prob[j],dicoEq1)
                            else :
                                liste_path[j] = probleme.coop_astar(liste_prob[j],dicoEq2) # Pour parcourir en Coop A*
                            print(liste_path[j])

                        # On remet à jour le compteur
                        liste_timer[j] = timer
                    

                # Dans le cas où le chemin est vide, on ajoute l'état final du joueur comme mur dans les problèmes de tout les joueurs 
                # (puisque le joueur reste statique désormais)
                if (len(liste_path[j]) == 0) :
                    for i in range(nbPlayers) :
                        liste_prob[i].grid[row][col] = False
            
            print ("Tour de jeu", it, "- Position joueur", j, ":", row,col)

            # On met à jour le score
            if (score[j] == 0) :
                if (row,col) == objectifs[j]:
                    score[j] += 1
                    print("Le joueur", j, " a atteint son but!")

                    # On met à jour le score des équipes
                    if players[j] in equipe1 :
                        score_eq1 += 1
                    if players[j] in equipe2 :
                        score_eq2 += 1

        # On passe a l'iteration suivante du jeu
        game.mainiteration()
        print()

        # On arrete le jeu dans le cas où une équipe a récupéré tout ses objectifs
        if (score_eq1 == effectifEquipe) and (score_eq2 != effectifEquipe) :
            # L'équipe 1 a gagné
            print("\nLes joueurs de l'équipe 1 ont tous récupéré leurs objectifs!\nScore Equipe 1 =", score_eq1, "\tScore Equipe 2 =", score_eq2)
            print("Temps de parcours total de l'équipe 1 :", sum(liste_temps[0:effectifEquipe]))
            print("Temps de parcours total de l'équipe 2 :", sum(liste_temps[effectifEquipe::]))
            break

        if (score_eq1 != effectifEquipe) and (score_eq2 == effectifEquipe) :
            # L'équipe 2 a gagné
            print("\nLes joueurs de l'équipe 2 ont tous récupéré leurs objectifs!\nScore Equipe 1 =", score_eq1, "\tScore Equipe 2 =", score_eq2)
            print("Temps de parcours total de l'équipe 1 :", sum(liste_temps[0:effectifEquipe]))
            print("Temps de parcours total de l'équipe 2 :", sum(liste_temps[effectifEquipe::]))
            break

        if (score_eq1 == effectifEquipe) and (score_eq2 == effectifEquipe) :
            # L'équipe 1 et 2 ont gagné en meme temps. Il y a égalité
            print("\nLes joueurs des deux équipes ont tous récupéré leurs objectifs!\nScore Equipe 1 =", score_eq1, "\tScore Equipe 2 =", score_eq2)
            print("Temps de parcours total de l'équipe 1 :", sum(liste_temps[0:effectifEquipe]))
            print("Temps de parcours total de l'équipe 2 :", sum(liste_temps[effectifEquipe::]))
            break

        # On actualise le nombre d'itérations
        it = it + 1
    
    print ("\nScores par joueur :", score)
    print("Temps de parcours par joueur :", liste_temps)
    pygame.quit()
    
       
    #-------------------------------


if __name__ == '__main__':
    main()
    


