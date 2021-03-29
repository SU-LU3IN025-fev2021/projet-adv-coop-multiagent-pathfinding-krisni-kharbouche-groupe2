# -*- coding: utf-8 -*-
"""
Created on Fri Feb 12 09:32:05 2016

@author: nicolas
"""

import numpy as np
import copy
import heapq
from abc import ABCMeta, abstractmethod
import functools
import time
import random


def distManhattan(p1,p2):
    """ calcule la distance de Manhattan entre le tuple 
        p1 et le tuple p2
        """
    (x1,y1)=p1
    (x2,y2)=p2
    return abs(x1-x2)+abs(y1-y2)

def cout(path) :
    """ Renvoie le cout du chemin du joueur passé en paramètre
        """
    return len(path)



    
###############################################################################

class Probleme(object):
    """ On definit un probleme comme étant: 
        - un état initial
        - un état but
        - une heuristique
        """
        
    def __init__(self,init,but,heuristique):
        self.init=init
        self.but=but
        self.heuristique=heuristique
        
    @abstractmethod
    def estBut(self,e):
        """ retourne vrai si l'état e est un état but
            """
        pass
        
    @abstractmethod    
    def cost(self,e1,e2):
        """ donne le cout d'une action entre e1 et e2, 
            """
        pass
        
    @abstractmethod
    def successeurs(self,etat):
        """ retourne une liste avec les successeurs possibles
            """
        pass
        
    @abstractmethod
    def immatriculation(self,etat):
        """ génère une chaine permettant d'identifier un état de manière unique
            """
        pass
    
    



###############################################################################

@functools.total_ordering # to provide comparison of nodes
class Noeud:
    def __init__(self, etat, g, pere=None):
        self.etat = etat
        self.g = g
        self.pere = pere
        
    def __str__(self):
        #return np.array_str(self.etat) + "valeur=" + str(self.g)
        return str(self.etat) + " valeur=" + str(self.g)
        
    def __eq__(self, other):
        return str(self) == str(other)
        
    def __lt__(self, other):
        return str(self) < str(other)
        
    def expand(self,p):
        """ étend un noeud avec ces fils
            pour un probleme de taquin p donné
            """
        nouveaux_fils = [Noeud(s,self.g+p.cost(self.etat,s),self) for s in p.successeurs(self.etat)]
        return nouveaux_fils
        
    def expandNext(self,p,k):
        """ étend un noeud unique, le k-ième fils du noeud n
            ou liste vide si plus de noeud à étendre
            """
        nouveaux_fils = self.expand(p)
        if len(nouveaux_fils)<k: 
            return []
        else: 
            return self.expand(p)[k-1]
            
    def trace(self,p):
        """ affiche tous les ancetres du noeud
            """
        n = self
        c=0    
        while n!=None :
            print (n)
            n = n.pere
            c+=1
        print ("Nombre d'étapes de la solution:", c-1)
        return            
        
        
###############################################################################
# A*
###############################################################################

def astar(p,verbose=False,stepwise=False):
    """
    application de l'algorithme a-star
    sur un probleme donné
        """
        
    startTime = time.time()

    nodeInit = Noeud(p.init,0,None)
    frontiere = [(nodeInit.g+p.h_value(nodeInit.etat,p.but),nodeInit)] 

    reserve = {}        
    bestNoeud = nodeInit
    
    while frontiere != [] and not p.estBut(bestNoeud.etat):              
        (min_f,bestNoeud) = heapq.heappop(frontiere)
           
    # VERSION 1 --- On suppose qu'un noeud en réserve n'est jamais ré-étendu
    # Hypothèse de consistence de l'heuristique        
        
        if p.immatriculation(bestNoeud.etat) not in reserve:            
            reserve[p.immatriculation(bestNoeud.etat)] = bestNoeud.g #maj de reserve
            nouveauxNoeuds = bestNoeud.expand(p)
            for n in nouveauxNoeuds:
                f = n.g+p.h_value(n.etat,p.but)
                heapq.heappush(frontiere, (f,n))

    # TODO: VERSION 2 --- Un noeud en réserve peut revenir dans la frontière        
        
        stop_stepwise=""
        if stepwise==True:
            stop_stepwise = input("Press Enter to continue (s to stop)...")
            print ("best", min_f, "\n", bestNoeud)
            print ("Frontière: \n", frontiere)
            print ("Réserve:", reserve)
            if stop_stepwise=="s":
                stepwise=False
    
            
    # Mode verbose            
    # Affichage des statistiques (approximatives) de recherche   
    # et les differents etats jusqu'au but
    if verbose:
        bestNoeud.trace(p)          
        print ("=------------------------------=")
        print ("Nombre de noeuds explorés", len(reserve))
        c=0
        for (f,n) in frontiere:
            if p.immatriculation(n.etat) not in reserve:
                c+=1
        print ("Nombre de noeuds de la frontière", c)
        print ("Nombre de noeuds en mémoire:", c + len(reserve))
        print ("temps de calcul:", time.time() - startTime)
        print ("=------------------------------=")
     
    n=bestNoeud
    path = []
    while n!=None :
        path.append(n.etat)
        n = n.pere

    print("A* - Temps de calcul:", time.time() - startTime)

    return path[::-1] # extended slice notation to reverse list

###############################################################################
# GREDDY BEST FIRST
# On établit deux listes de Noeud (une liste de noeuds ouverts et une liste de noeuds fermés)
# Les noeuds ouverts sont ceux que l'on étudie
# Les noeuds fermés sont ceux que l'on a déjà étudié
# Le but est d'étudier le noeud le plus prometteur dans la liste des noeuds ouverts
# Prometteur = meilleure distance heuristique par rapport au but (distance de Manhantan)
###############################################################################

def greedyBestFirst(p) :
    """
    application de l'algorithme Greedy Best First
    sur un probleme donné
    """

    startTime = time.time() # On commence le timer

    openNodes = list() # Liste des noeuds ouverts
    closedNodes = list() # Liste des noeuds fermés

    nodeInit = Noeud(p.init,0,None) # Noeud initial
    openNodes.append(nodeInit) # On ajoute le noeud initial aux noeuds ouverts
    bestNode = nodeInit # Best node est le noeud en cours d'utilisation

    # Etapes de l'algo de recherche
    # 1) On vérifie si le noeud en cours est l'objectif
    # 2) Si non :
    #   - on ajoute tout les noeuds voisins du noeud en cours dans la liste des noeuds ouverts (si ils ne sont pas déjà présent dans une des deux listes)
    #   - on ajoute dans la liste des noeuds fermés le noeud en cours
    #   - on cherche dans la liste des noeuds ouverts le noeud le plus prometteur
    #   - on passe le noeud prometteur en tant que noeud en cours
    #   - on répète le procédé
    # 3) Si oui :
    #   - on arrete l'algorithme de recherche
    #   - on renvoie le chemin du noeud en cours (soit le noeud but) jusqu'au noeud racine (noeud.pere == None)
    # Attention : si à un moment donné, la liste des noeuds ouverts est vide, cela signifie que le probleme est sans résolution
    
    while (openNodes != []) and (not p.estBut(bestNode.etat)) :
        # On ajoute le meilleur noeud à la liste des noeuds fermés et on le retire de la liste des noeuds ouverts
        closedNodes.append(bestNode)
        openNodes.remove(bestNode)

        # Crée la liste des voisins du meilleur Noeud
        nouveauxNoeuds = bestNode.expand(p)

        # On ajoute les noeuds voisins du meilleur noeud à la liste des noeuds ouverts
        for n in nouveauxNoeuds :
            liste_etats = list()

            for e in openNodes :
                liste_etats.append(e.etat)
            for e in closedNodes :
                liste_etats.append(e.etat)

            if (n.etat not in liste_etats) :
                openNodes.append(n)

        # On cherche le noeud optimal parmi les noeuds ouverts
        newBestNode = openNodes[0]
        for n in openNodes[1::] :
            # On compare les deux noeuds et si le noeud n est plus optimal que le meilleur noeud, newBestNode = n (avec la distance de Manhantan)
            if (distManhattan(n.etat, p.but) < distManhattan(newBestNode.etat, p.but)) : 
                newBestNode = n
        bestNode = newBestNode

    # On renvoie le chemin jusqu'au but
    n = bestNode
    path = []

    while n != None :
        path.append(n.etat)
        n = n.pere

    print("Greedy Best First - Temps de calcul:", time.time() - startTime)
    
    return path[::-1]


###############################################################################
# RANDOM BEST FIRST
###############################################################################

def randomBestFirst(p) :
    """
    application de l'algorithme Random Best First
    sur un probleme donné
    """

    startTime = time.time() # On commence le timer

    openNodes = list() # Liste des noeuds ouverts
    closedNodes = list() # Liste des noeuds fermés

    nodeInit = Noeud(p.init,0,None) # Noeud initial
    openNodes.append(nodeInit) # On ajoute le noeud initial aux noeuds ouverts
    bestNode = nodeInit # Best node est le noeud en cours d'utilisation

    # Etapes de l'algo de recherche
    # 1) On vérifie si le noeud en cours est l'objectif
    # 2) Si non :
    #   - on ajoute tout les noeuds voisins du noeud en cours dans la liste des noeuds ouverts (si ils ne sont pas déjà présent dans une des deux listes)
    #   - on ajoute dans la liste des noeuds fermés le noeud en cours
    #   - on choisit comme nouveau noeud prometteur le premier noeud de la liste des noeuds ouverts
    #   - on passe le noeud prometteur en tant que noeud en cours
    #   - on répète le procédé
    # 3) Si oui :
    #   - on arrete l'algorithme de recherche
    #   - on renvoie le chemin du noeud en cours (soit le noeud but) jusqu'au noeud racine (noeud.pere == None)
    # Attention : si à un moment donné, la liste des noeuds ouverts est vide, cela signifie que le probleme est sans résolution
    
    while (openNodes != []) and (not p.estBut(bestNode.etat)) :
        # On ajoute le meilleur noeud à la liste des noeuds fermés et on le retire de la liste des noeuds ouverts
        closedNodes.append(bestNode)
        openNodes.remove(bestNode)

        # Crée la liste des voisins du meilleur Noeud
        nouveauxNoeuds = bestNode.expand(p)

        # On ajoute les noeuds voisins du meilleur noeud à la liste des noeuds ouverts
        for n in nouveauxNoeuds :
            liste_etats = list()

            for e in openNodes :
                liste_etats.append(e.etat)
            for e in closedNodes :
                liste_etats.append(e.etat)

            if (n.etat not in liste_etats) :
                openNodes.append(n)

        # Le nouveau noeud optimal est le premier de la liste des noeuds ouverts
        randV = random.randint(0, len(openNodes) - 1)
        bestNode = openNodes[randV]

    # On renvoie le chemin jusqu'au but
    n = bestNode
    path = []

    while n != None :
        path.append(n.etat)
        n = n.pere

    print("Random Best First - Temps de calcul:", time.time() - startTime)

    return path[::-1]

###############################################################################
# AUTRES ALGOS DE RESOLUTIONS...
###############################################################################

###############################################################################
# GREDDY BEST FIRST
# On établit deux listes de Noeud (une liste de noeuds ouverts et une liste de noeuds fermés)
# Les noeuds ouverts sont ceux que l'on étudie
# Les noeuds fermés sont ceux que l'on a déjà étudié
# Le but est d'étudier le noeud le plus prometteur dans la liste des noeuds ouverts
# Prometteur = meilleure distance heuristique par rapport au but (distance de Manhantan)
###############################################################################
