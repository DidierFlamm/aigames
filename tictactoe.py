#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 21 15:34:08 2025

@author: did
"""

from game import Game
from typing import List, Any
import random
from time import time
from copy import deepcopy

# State est une liste représentant les valeurs des 9 cases du board : 'X', 'O', ou ' ' 
StateType = List[str]

# Move est un string représentant l'index de la case jouée : de "0" à "8" selon la grille ci-dessous

#	╔═══╦═══╦═══╗
#	║ 0 ║ 1 ║ 2 ║
#	╠═══╬═══╬═══╣
#	║ 3 ║ 4 ║ 5 ║
#	╠═══╬═══╬═══╣
#	║ 6 ║ 7 ║ 8 ║
#	╚═══╩═══╩═══╝

class TicTacToe(Game):

    WINNING_COMBINATIONS = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # lignes
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # colonnes
        [0, 4, 8], [2, 4, 6]              # diagonales
    ]
    
    def __init__(self, initial_state: StateType = [' '] * 9, all_against_ref_player = True):
        super().__init__(initial_state, all_against_ref_player)
        
        #pre-start : création des 2 joueurs via UI sans demander le nb de joueurs et avec symboles par défaut
        self.nb_players = 2
        self.managerUI.new_player(symbol = "X", color = "cyan")
        self.managerUI.new_player(symbol = "O", color = "red")
        
    def print_help(self):
        print("How to play:")
        print("- Choose a move by entering a number corresponding to the board position.")
        print("- Positions are numbered from left to right, top to bottom, as shown below:")
        self.print_state(["0","1","2","3","4","5","6","7","8"])
        print("- For example, '0' is the top-left cell, '8' is the bottom-right.")
        print("- Type '?' or 'help' to display these instructions again.")
    
    def is_terminal(self, state: StateType) -> bool:
        return self.get_winner_by_symbol(state) is not None or ' ' not in state
    
    def get_winner_by_symbol(self, state: StateType) -> str | None:

        for combo in self.WINNING_COMBINATIONS:
            a, b, c = combo
            if state[a] != ' ' and state[a] == state[b] == state[c]:
                return state[a]
        return None

    def get_score_by_symbol(self, state: StateType, reference_player_symbol: str, depth: int) -> int:

        """
        Retourne un score estimé pour l'état final du jeu en fonction du résultat du jeu : victoire, défaite ou égalité.
    
        - Si le joueur de référence a gagné, le score (entre 50 et 10) est élevé et dépend de la rapidité de la victoire (profondeur faible = score élevé).
        - Si le joueur de référence a perdu, le score est négatif (entre -50 et -10), avec une pénalité moins sévère à mesure que la profondeur augmente.
        - En cas de match nul, le score (0=<s<=9) est basé sur les cases occupées par le joueur de référence :
          - Le centre est favorisé (+5 points),
          - Les coins sont légèrement favorisés (+1 point),
          - Les bords ne sont pas privilégiés (score de 0).
    
        Le score retourné est conçu pour favoriser les victoires rapides et les positions stratégiques (centre, coins).
    
        Paramètres:
        - state (StateType) : L'état actuel du jeu, représenté sous forme de liste ou tableau.
        - reference_player_symbol (str) : Le joueur de référence pour lequel le score est calculé (le joueur actif).
        - depth (int) : La profondeur actuelle dans l'arbre de recherche Minimax.
    
        Retourne:
        - int : Le score estimé pour l'état final. Le score peut être positif pour une victoire, négatif pour une défaite et basé sur les cases occupées pour une égalité.
        """
        
        #NB : il faut toujours s'assurer dans cette méthode que victoire > égalité > défaite
        
        winner_symbol = self.get_winner_by_symbol(state)
        
        if winner_symbol == reference_player_symbol:
            # Le score est plus élevé pour une victoire rapide, décroît avec la profondeur
            return 10 * (10 - depth)  # Score entre 50 (victoire rapide) et 10 (victoire lente)
        
        elif winner_symbol == self.get_next_player_by_symbol(reference_player_symbol):
            # Le score est plus négatif pour une défaite rapide, devient moins négatif avec la profondeur
            return -10 * (10 - depth)  # Score entre -10 (défaite lente) et -50 (défaite rapide)
        
        else:                                               # match nul
            score = 0
            for i in range(9):
                if state[i]==reference_player_symbol:              #on balaie les cases du joueur de référence
                    if i == 4 : score+=5                    # 5 points pour le centre (plus important)
                    if i in [0,2,6,8]: score +=1            # 1 point pour les coins (moins important que le centre mais plus que les bords qui valent 0)
            return score
        
    def get_heuristic_by_symbol(self, state: StateType, reference_player_symbol: str, depth: int) -> int:
        # Évaluation simple (peut être améliorée)
        score = 0
        
        # Lignes presque gagnantes (2 cases sur 3) : +ou- 1 point
        for combo in self.WINNING_COMBINATIONS:
            line = [state[i] for i in combo]
            if line.count(reference_player_symbol) == 2 and line.count(' ') == 1:
                score += 1
            elif line.count(self.get_next_player_by_symbol(reference_player_symbol)) == 2 and line.count(' ') == 1:
                score -= 1
                
        # Le contrôle du centre est implicitement pris en compte car il appartient à 4 combos différents...
        # mais on peut l'accentuer pour forcer le minimax a prendre le centre si il manque de profondeur d'évaluation
        # +ou- 1 point        
        if state[4] == reference_player_symbol:
            score += 1
        elif state[4] == self.get_next_player_by_symbol(reference_player_symbol):
            score -= 1
        
        return score
    
    def get_possible_moves(self, state: StateType) -> List[str]:
        return [str(i) for i in range(9) if state[i] == ' ']
                                
    def apply_move(self, state: StateType, move: str, player) -> StateType:
        
        new_state = deepcopy(state)                     # deepcopy par précaution : au cas où l'on utilise des listes de listes (multi tictactoe)
        
        new_state[int(move)] = player.symbol
        return new_state
        
    def state_to_str(self, state: StateType) -> str:
        return "".join(state)
    
    def print_state_from_str(self, state : str) -> None:
        
        
        print("\t╔═══╦═══╦═══╗")
        print("\t║", state[0], "║",state[1] , "║" ,state[2],  "║")
        print("\t╠═══╬═══╬═══╣")
        print("\t║", state[3], "║",state[4] , "║" ,state[5],  "║")
        print("\t╠═══╬═══╬═══╣")
        print("\t║", state[6], "║",state[7] , "║" ,state[8],  "║")
        print("\t╚═══╩═══╩═══╝")
    
    
    def print_colored_state(self, state : StateType, players : List[Any]):
        
        colored_state = [self.symbol_to_colored_symbol(case,players) for case in state]
        
        self.print_state_from_str(colored_state)

                   
    def early_pruning(self, state, depth, value, max_depth=None, reference_player=None):
        """
        Early Pruning spécifique au TicTacToe
        Détermine si l'on peut arrêter l'exploration plus tôt pour ce jeu.
        On arrête dès qu'on trouve une victoire rapide (score == 50) ou une défaite rapide (score == -50) c'est à dire en 5 coups
        """
        return value == 50 or value == -50  # victoire ou défaite rapide



#TicTacToePlus

# Move est un string calqué sur la disposition du pavé numérique
# De plus, l'utilisateur peut laisser l'IA joué à sa place si il ne saisit pas de coup

#	╔═══╦═══╦═══╗
#	║ 7 ║ 8 ║ 9 ║
#	╠═══╬═══╬═══╣
#	║ 4 ║ 5 ║ 6 ║
#	╠═══╬═══╬═══╣
#	║ 1 ║ 2 ║ 3 ║
#	╚═══╩═══╩═══╝

class TicTacToePlus(TicTacToe):
    
    def __init__(self, initial_state: StateType = [' '] * 9, all_against_ref_player = True):
        #appel de l'init de Game et non de TicTacToe pour ne pas court-circuiter l'ajout du bot
        Game.__init__(self, initial_state, all_against_ref_player)
        
        #ajout d'un best bot + rapide que l'on insère en 1ère position des bot_fns
        self.bot_move_fns = {'faster_best_move': self.get_best_move_faster, **self.bot_move_fns}
        
        #pre-start identique à la classe TicTacToe (mais qu'il faut appeler après avoir ajouté le bot...)
        self.nb_players = 2
        self.managerUI.new_player(symbol = "X", color = "cyan")
        self.managerUI.new_player(symbol = "O", color = "red")


    
    def print_help(self):
        print("How to play:")
        print("- Choose a move by entering a number corresponding to the board position.")
        print("- Positions are numbered from left to right, top to bottom, as shown below:")
        self.print_state_from_str(["7","8","9","4","5","6","1","2","3"])
        print("- For example, '7' is the top-left cell, '3' is the bottom-right.")
        print("- Press [Enter] without typing anything to let the AI play for you.")
        print("- Type '?' or 'help' to display these instructions again.")

    
    def get_possible_moves_faster(self, state: StateType) -> List[str]:
        """plus rapide que get_possible_moves car optimise le temps de calcul des 3 premiers coups en limitant aux possibilités optimales
        on va l'obliger à choisir de préférence le centre puis les coins puis les bords en cas d'égalité d'evaluate...
        """ 
        center = ["4"]
        coins = ["0", "2", "6", "8"]
        random.shuffle(coins)           #on randomize coins
        bords = ["1", "3", "5", "7"]
        random.shuffle(bords)           #on randomize bords
        
        order = center + coins + bords 
        
        #réduction des possibles moves pour tenir compte des meilleurs 1ers et 2emes coups
        #réduis le temps du 1er coup de 2300 ms à 37ms et celui du 2eme coup de 230ms à 37ms
        #ce temps pourrait être encore réduit en optimisant le 3eme coup (qui dure aussi 37 ms...)

        
        if state[4]== " ":          #1er coup et 2eme coup si le centre est libre : on prend le centre
            return center
        
        if state.count(" ")== 8:    #2eme coup si le centre est pris : on prend 1 coin
            return coins[0]
        
        if state.count(" ")== 7:    #3eme coup : si je joue le 3eme coup c'est que j'ai joué le 1er coup donc j'ai le centre
                                    #2 possibilités : l'adversaire a joué un coin => je prends un coin adjacent (menace sur diagonale)
                                    #                 l'adversaire a joué un bord => je prends un coin adjacent 
            if state[0] != " ":
                adj_coins = ["2", "6"]
            elif state[1] != " ":
                adj_coins = ["0", "2"]
            elif state[2] != " ":
                adj_coins = ["0", "8"]
            elif state[3] != " ":
                adj_coins = ["0", "6"]
            elif state[5] != " ":
                adj_coins = ["2", "8"]
            elif state[6] != " ":
                adj_coins = ["0", "8"]
            elif state[7] != " ":
                adj_coins = ["6", "8"]
            elif state[8] != " ":
                adj_coins = ["2", "6"]
                
            random.shuffle(adj_coins)
            return adj_coins[0]
        
        #sinon on teste toutes les cases == ' ' dans l'ordre centre + coins + bords        
        
        return [i for i in order if state[int(i)] == ' ']
    
    
    def get_human_move(self, state, player, **kwargs)-> str:
        """ 
        Surcharge de la méthode de classe notamment pour :
            -transformer l'entrée calquée sur les touches du pavé numérique (entre 1 et 9) au format requis par move (entre 0 et 8) 
            -rajouter la fonction best_move IA
        NB: **kwargs permet de le rendre compatible avec best_move
        """
        
        current_colored_symbol = self.get_colored_symbol(player)
        
        human_input = input(f"{self.current_player.name} : {current_colored_symbol} – Your turn ! Move or '?' for help ➤ ")
        
        human_input_to_move = {"1":"6", "2":"7", "3":"8", "4":"3", "5":"4", "6":"5", "7":"0", "8":"1", "9":"2"}
        
        move = human_input_to_move.get(human_input, human_input)
        
        moves = self.get_possible_moves(state)
        duration = None
        
        if move == "" :      #IA calcule le best_move pour le joueur en cours ainsi que le temps de calcul en ms
            t_start = time()
            best_move = self.get_best_move_faster(state=state, player=player, reference_player=player, all_against_ref_player=True, max_depth=None)
            # le best move est calculé en minimax classique : le ref_player est le player courant (alterne à chaque tour), et all_agains_ref = True
            duration = int(1000*(time() - t_start))
            print("AI played move", best_move, "in", duration, "ms")
            return best_move
            
        elif move == "?" or move == "help":
            self.print_help()
            return self.get_human_move(state, player)
                              
        elif not move.isdigit():
            print(f"{move} is not a valid number! Please enter a valid number.")
            return self.get_human_move(state, player)
            
        elif move not in moves:
            print(f"{human_input} is not a valid move !")
            return self.get_human_move(state, player)
        else:
            return move
        
    def get_best_move_faster(self, state: StateType, player, reference_player, all_against_ref_player, max_depth: int) -> str:
        """
        Utilise get_possible_moves_faster au lieu de get_possible_moves
             et minimax_fatser au lieu de minimax
        """
        
        best_move = None
        if all_against_ref_player:
            best_value = -float('inf') if player == reference_player else float('inf')
        else:
            best_value = -float('inf')
    
        # Calcul du value pour chaque move possible
        for move in self.get_possible_moves_faster(state):
            next_state = self.apply_move(state, move, player)
            value = self.minimax_faster(next_state, self.get_next_player(player), reference_player, 1, max_depth)  # depth initialisé à 1, sera incrémenté à chaque appel de minimax
    
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
    
    def minimax_faster(self, state, player, reference_player, depth, max_depth=None) -> int:
        """
        Utilise get_possible_moves_faster au lieu de de get_possible_moves
        """
        
        if self.is_terminal(state):                                         #si le state est terminal, on renvoie le score de state
            return self.get_score_by_symbol(state, reference_player.symbol, depth)           #get_score et arrêt de l'exploration de la branche
                
        if max_depth is not None and depth >= max_depth:                    #si max_depth est définie et atteinte (ou dépassée)
                return self.get_heuristic_by_symbol(state, reference_player.symbol, depth)   #get_heuristic et arrêt de l'exploration de la branche   
        
    
        # Initialisation du best_score si le joueur maximise ou minimise en fonction de la référence
        best_value = -float('inf') if player == reference_player else float('inf')
    
        # Exploration des moves possibles
        for move in self.get_possible_moves_faster(state):                #pour chaque move possible, on calcule l'état engendré et son score optimal par Minimax
            next_state = self.apply_move(state, move, player)
            value = self.minimax_faster(next_state, self.get_next_player(player), reference_player, depth + 1, max_depth)
            
            #Mise à jour de la best_value
            if player == reference_player:
                best_value = max(best_value, value)  # Maximiser pour le joueur de référence            
            else:
                best_value = min(best_value, value)  # Minimiser pour l'autre joueur
                
            if self.early_pruning_hook(next_state, depth + 1, value, max_depth, reference_player):
                break # Arrêt précoce si la condition d'élagage est remplie
    
        return best_value

if __name__ == "__main__":
    my_game = TicTacToePlus()        #use TicTacToe() instead of TicTacToePlus() for standard version 
    my_game.start(log=True)          #start and log game
    my_game.replay()                 #choose your log to view replay