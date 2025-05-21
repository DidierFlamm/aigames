# -*- coding: utf-8 -*-
"""
Created on Mon May 12 09:38:44 2025

@author: did

exemple : https://www.codingame.com/multiplayer/bot-programming/tic-tac-toe
 
"""

#TODO: DRY (Don’t Repeat Yourself) factoriser minimax_classique et selfish : code long et bcp de redondance dans les 2 méthodes
#TODO: créer version alpha beta du minimax: minimax_ab()


class Minimax:
    def __init__(self, game):
        self.game = game
        
    def get_best_move(self, state, player, reference_player, all_against_ref_player, max_depth: int) -> str:
        """
        Fonction qui détermine le meilleur coup à jouer pour un joueur donné en fonction de l'algorithme Minimax.
        
        Cette fonction choisit dynamiquement quel type de Minimax utiliser en fonction de la situation du jeu grâce à la méthode _minimax.
        
        Parameters:
        - state : L'état actuel du jeu.
        - player : Le joueur pour lequel nous déterminons le meilleur coup.
        - reference_player : Le joueur de référence (utilisé si `all_against_ref_player` est True).
        - max_depth : La profondeur maximale pour l'algorithme Minimax (utiliser None pour ne pas limiter Minimax en profondeur).
        - all_against_ref_player : Un booléen qui indique si tous les joueurs sont contre le joueur de référence (True) ou si chaque joueur maximise son propre score indépendamment (False).
        
        Returns:
        - Le meilleur coup pour le joueur donné.
        """
        
        best_move = None
        if all_against_ref_player:
            best_value = -float('inf') if player == reference_player else float('inf')
        else:
            best_value = -float('inf')
    
        # Calcul du value pour chaque move possible
        for move in self.game.get_possible_moves(state):
            next_state = self.game.apply_move(state, move, player)
            value = self.minimax(next_state, self.game.get_next_player(player), reference_player, all_against_ref_player, 1, max_depth)  # depth initialisé à 1, sera incrémenté à chaque appel de minimax
    
            # Mise à jour de best_value et best_move selon all_against_ref_player et le player
            if all_against_ref_player:    
                if player == reference_player:
                    if value > best_value:
                        best_value = value
                        best_move = move
                else:
                    if value < best_value:
                        best_value = value
                        best_move = move
            else:
                if value > best_value:
                    best_value = value
                    best_move = move
    
        return best_move    
    

    def minimax(self, state, player, reference_player, all_against_ref_player, depth, max_depth=None):
        """
        Choisit dynamiquement la stratégie Minimax à utiliser selon le mode de jeu :
        
        - Si all_against_ref_player est True, les autres joueurs sont considérés comme jouant contre reference_player 
          (stratégie classique Minimax, souvent utilisée pour 2 joueurs).
        
        - Si all_against_ref_player est False, chaque joueur maximise son propre score (stratégie selfish plus réaliste pour les jeux à plusieurs joueurs).
    
        Parameters:
        - state: L'état actuel du jeu
        - player: Le joueur actuel
        - reference_player: Le joueur cible pour la stratégie classique (à maximiser ou minimiser)
        - all_against_ref_player: Booléen contrôlant le mode de stratégie
        - depth: La profondeur actuelle dans l'arbre de recherche
        - max_depth: La profondeur maximale d'exploration (None = sans limite)
    
    
        Returns:
        - Le score estimé du coup joué à partir de cet état
        """
        
        if all_against_ref_player:
            return self.minimax_classic(state, player, reference_player, depth, max_depth)
        else:
            return self.minimax_selfish(state, player, depth, max_depth)
    
    
    def minimax_classic(self, state, player, reference_player, depth, max_depth=None) -> int:
        """
        Stratégie Minimax classique pour les jeux où tous les joueurs s'opposent à reference_player :
        - reference_player cherche à maximiser son score
        - les autres joueurs cherchent à le minimiser
        
        Le parcours s'arrête :
        - si l'état est terminal (victoire, défaite, égalité…)
        - ou si la profondeur maximale est atteinte, auquel cas une heuristique est utilisée.
        
        Une fonction d’élagage personnalisée `early_pruning` peut être appelée pour interrompre
        plus tôt certaines branches, selon des critères définis par l'utilisateur. 
        L’élagage est facultatif : si `early_pruning` n'est pas implémentée ou toujours False, 
        l'algorithme parcourt l'intégralité de l'arbre.
        
        Parameters:
        - state: L'état actuel du jeu.
        - player: Le joueur en cours.
        - reference_player: Le joueur cible de la stratégie (qu'on cherche à maximiser ou minimiser).
        - depth: Profondeur actuelle dans l'arbre de recherche.
        - max_depth: Profondeur maximale d'exploration (None = sans limite).
        
        Returns:
        - Le score estimé optimal à partir de cet état.
        """
        
        if self.game.is_terminal(state):                                         #si le state est terminal, on renvoie le score de state
            return self.game.get_score_by_symbol(state, reference_player.symbol, depth)           #get_score et arrêt de l'exploration de la branche
                
        if max_depth is not None and depth >= max_depth:                    #si max_depth est définie et atteinte (ou dépassée)
                return self.game.get_heuristic_by_symbol(state, reference_player.symbol, depth)   #get_heuristic et arrêt de l'exploration de la branche   
        
    
        # Initialisation du best_score si le joueur maximise ou minimise en fonction de la référence
        best_value = -float('inf') if player == reference_player else float('inf')
    
        # Exploration des moves possibles
        for move in self.game.get_possible_moves(state):                #pour chaque move possible, on calcule l'état engendré et son score optimal par Minimax
            next_state = self.game.apply_move(state, move, player)
            value = self.minimax_classic(next_state, self.game.get_next_player(player), reference_player, depth + 1, max_depth)
            
            #Mise à jour de la best_value
            if player == reference_player:
                best_value = max(best_value, value)  # Maximiser pour le joueur de référence            
            else:
                best_value = min(best_value, value)  # Minimiser pour l'autre joueur
                
            if self.game.early_pruning_hook(next_state, depth + 1, value, max_depth, reference_player):
                break # Arrêt précoce si la condition d'élagage est remplie
    
        return best_value
    

    
    
    
    def minimax_selfish(self, state, player, depth: int, max_depth=None) -> int:
        """
        Stratégie Minimax pour les jeux à plusieurs joueurs où chaque joueur
        cherche uniquement à maximiser son propre score, indépendamment des autres.
    
        Cette approche suppose que tous les joueurs sont égoïstes (selfish) :
        ils ne cherchent ni à coopérer ni à nuire à un joueur en particulier (comme reference_player).
    
        L’exploration s’arrête si :
        - l’état est terminal (victoire, défaite, égalité...)
        - la profondeur maximale est atteinte (utilisation d'une heuristique)
        - la fonction d’élagage précoce `early_pruning_hook` le recommande
    
        Paramètres :
        - state : état actuel du jeu
        - player : joueur actif
        - depth : profondeur actuelle dans l’arbre
        - max_depth : profondeur maximale autorisée
    
        Retour :
        - score estimé maximal pour le joueur actuel
        """
        
        # contrairement au minimax classique, on calcule ici le score de chaque état pour le player en cours (qu'il va chercher a maximiser) et non le score de ref_player (qui sera miner ou maxer selon le player en cours)
        
        # Si l'état est terminal, on retourne le score du joueur actif
        if self.game.is_terminal(state):
            return self.game.get_score_by_symbol(state, player.symbol, depth)
        
        # Si on atteint la profondeur maximale, on retourne l'heuristique
        if max_depth is not None and depth >= max_depth:
            return self.game.get_heuristic_by_symbol(state, player.symbol, depth)
    
        # Chaque joueur cherche à maximiser son propre score
        best_value = -float('inf')
        
        for move in self.game.get_possible_moves(state):
            next_state = self.game.apply_move(state, move, player)
            value = self.minimax_selfish(next_state, self.game.get_next_player(player), depth + 1, max_depth)
            best_value = max(best_value, value)  # Maximisation pour le joueur actuel
    
            if self.game.early_pruning_hook(next_state, depth + 1, value, max_depth, reference_player=None):
                break  # Arrêt précoce si la condition d'élagage est remplie
    
        return best_value
    
    
    
    
